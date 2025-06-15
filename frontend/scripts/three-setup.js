// Three.js Scene Setup and Management

class ThreeJSManager {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.axesHelper = null;
        this.gridHelper = null;
        this.polarGridHelper = null;
        this.animationEnabled = false;
        this.wireframeMode = false;
        this.modelBuilder = new ModelBuilder();
        
        // Grid and visual aids toggles
        this.gridVisible = true;
        this.axesVisible = true;
        this.polarGridVisible = false;
        this.navigationCube = null;
    }

    init(containerId) {
        try {
            this.scene = new THREE.Scene();
            
            // Blender-style background: dark gradient from top to bottom
            const loader = new THREE.TextureLoader();
            this.scene.background = new THREE.Color(0x1e1e1e); // Very dark gray like Blender
            
            this.camera = new THREE.PerspectiveCamera(45, 1, 0.01, 100000);
            this.camera.position.set(7.36, 4.96, 6.93); // Default Blender camera position
            this.camera.lookAt(0, 0, 0);

            this.renderer = new THREE.WebGLRenderer({ 
                antialias: true,
                alpha: true,
                powerPreference: "high-performance"
            });
            this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            this.renderer.shadowMap.enabled = true;
            this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            this.renderer.outputColorSpace = THREE.SRGBColorSpace;
            this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
            this.renderer.toneMappingExposure = 1.0; // Blender-like exposure
            
            // Blender-style rendering settings
            this.renderer.physicallyCorrectLights = true;
            this.renderer.shadowMap.autoUpdate = true;
            
            // Blender-style rendering settings
            this.renderer.physicallyCorrectLights = true;
            this.renderer.shadowMap.autoUpdate = true;

            const viewport = document.getElementById(containerId);
            viewport.appendChild(this.renderer.domElement);

            this.setupLighting();
            this.setupControls();
            this.setupGridsAndAxes();
            this.createNavigationCube();
            this.resizeRenderer();
            this.animate();

            console.log('🚀 Three.js initialized with Blender-style setup');
            return true;
        } catch (error) {
            console.error('❌ Three.js initialization error:', error.message);
            return false;
        }
    }

    setupLighting() {
        // Blender-style lighting setup: clean and minimal
        // Main ambient light (soft overall illumination)
        const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
        this.scene.add(ambientLight);

        // Key light (main directional light from top-right)
        const keyLight = new THREE.DirectionalLight(0xffffff, 1.0);
        keyLight.position.set(10, 10, 5);
        keyLight.castShadow = true;
        keyLight.shadow.mapSize.width = 2048;
        keyLight.shadow.mapSize.height = 2048;
        keyLight.shadow.camera.near = 0.1;
        keyLight.shadow.camera.far = 1000;
        keyLight.shadow.camera.left = -200;
        keyLight.shadow.camera.right = 200;
        keyLight.shadow.camera.top = 200;
        keyLight.shadow.camera.bottom = -200;
        keyLight.shadow.bias = -0.0001;
        this.scene.add(keyLight);

        // Subtle fill light (opposite side, much weaker)
        const fillLight = new THREE.DirectionalLight(0x87ceeb, 0.3);
        fillLight.position.set(-5, 3, -5);
        this.scene.add(fillLight);
        
        // Add Blender-style HDRI environment
        this.setupEnvironment();
    }

    setupEnvironment() {
        // Create a simple environment map for reflections
        const pmremGenerator = new THREE.PMREMGenerator(this.renderer);
        
        // Create a simple gradient environment
        const envScene = new THREE.Scene();
        const envGeometry = new THREE.SphereGeometry(50, 32, 16);
        const envMaterial = new THREE.MeshBasicMaterial({
            color: 0x2a2a2a,
            side: THREE.BackSide
        });
        const envSphere = new THREE.Mesh(envGeometry, envMaterial);
        envScene.add(envSphere);
        
        const envMap = pmremGenerator.fromScene(envScene).texture;
        this.scene.environment = envMap;
        
        // Clean up
        pmremGenerator.dispose();
        envScene.clear();
    }

    setupControls() {
        let mouseDown = false;
        let rightMouseDown = false;
        let mouseX = 0;
        let mouseY = 0;
        let panSpeed = 0.002;
        let rotateSpeed = 0.01;
        let zoomSpeed = 0.04;

        const canvas = this.renderer.domElement;

        // Blender-style controls
        canvas.addEventListener('mousedown', (event) => {
            event.preventDefault();
            if (event.button === 0) { // Left mouse button - orbit
                mouseDown = true;
            } else if (event.button === 2) { // Right mouse button - pan
                rightMouseDown = true;
            }
            mouseX = event.clientX;
            mouseY = event.clientY;
        });

        canvas.addEventListener('mouseup', (event) => {
            mouseDown = false;
            rightMouseDown = false;
        });

        canvas.addEventListener('contextmenu', (event) => {
            event.preventDefault(); // Disable right-click context menu
        });

        canvas.addEventListener('mousemove', (event) => {
            if (mouseDown || rightMouseDown) {
                const deltaX = event.clientX - mouseX;
                const deltaY = event.clientY - mouseY;

                if (mouseDown) {
                    // Orbit camera around target (Blender-style rotation)
                    const spherical = new THREE.Spherical();
                    spherical.setFromVector3(this.camera.position);
                    spherical.theta -= deltaX * rotateSpeed;
                    spherical.phi += deltaY * rotateSpeed;
                    spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi));

                    this.camera.position.setFromSpherical(spherical);
                    this.camera.lookAt(0, 0, 0);
                } else if (rightMouseDown) {
                    // Pan camera (Blender-style middle mouse)
                    const distance = this.camera.position.distanceTo(new THREE.Vector3(0, 0, 0));
                    const panX = -deltaX * panSpeed * distance;
                    const panY = deltaY * panSpeed * distance;
                    
                    // Get camera's local axes
                    const right = new THREE.Vector3();
                    const up = new THREE.Vector3();
                    this.camera.getWorldDirection(right);
                    right.cross(this.camera.up).normalize();
                    up.copy(this.camera.up);
                    
                    // Move camera position
                    this.camera.position.addScaledVector(right, panX);
                    this.camera.position.addScaledVector(up, panY);
                }

                mouseX = event.clientX;
                mouseY = event.clientY;
            }
        });

        canvas.addEventListener('wheel', (event) => {
            event.preventDefault();
            
            // Blender-style zoom towards cursor
            const distance = this.camera.position.distanceTo(new THREE.Vector3(0, 0, 0));
            const zoomDelta = event.deltaY * zoomSpeed;
            const newDistance = distance + zoomDelta;
            const clampedDistance = Math.max(0.1, Math.min(10000, newDistance));
            
            this.camera.position.normalize().multiplyScalar(clampedDistance);
        });

        // Add keyboard shortcuts for Blender-style navigation
        document.addEventListener('keydown', (event) => {
            // Numpad navigation like Blender
            switch(event.code) {
                case 'Numpad7': // Top view
                    this.camera.position.set(0, 10, 0);
                    this.camera.lookAt(0, 0, 0);
                    event.preventDefault();
                    break;
                case 'Numpad1': // Front view
                    this.camera.position.set(0, 0, 10);
                    this.camera.lookAt(0, 0, 0);
                    event.preventDefault();
                    break;
                case 'Numpad3': // Right view
                    this.camera.position.set(10, 0, 0);
                    this.camera.lookAt(0, 0, 0);
                    event.preventDefault();
                    break;
            }
        });
    }

    setupGridsAndAxes() {
        // Blender-style axes helper (smaller and more subtle)
        this.axesHelper = new THREE.AxesHelper(3);
        this.axesHelper.visible = this.axesVisible;
        this.scene.add(this.axesHelper);

        // Create infinite grid shader (Blender-style)
        this.createInfiniteGrid();
        
        // Optional traditional grids (hidden by default)
        this.createOptionalGrids();
    }

    createInfiniteGrid() {
        // Blender-style infinite grid shader
        const vertexShader = `
            varying vec3 vWorldPosition;
            varying vec3 vPosition;
            
            void main() {
                vPosition = position;
                vec4 worldPosition = modelMatrix * vec4(position, 1.0);
                vWorldPosition = worldPosition.xyz;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `;

        const fragmentShader = `
            varying vec3 vWorldPosition;
            varying vec3 vPosition;
            uniform float uTime;
            uniform vec3 uCameraPosition;
            
            float getGrid(vec2 coords, float scale) {
                vec2 grid = abs(fract(coords * scale - 0.5) - 0.5) / fwidth(coords * scale);
                float line = min(grid.x, grid.y);
                return 1.0 - min(line, 1.0);
            }
            
            void main() {
                float distanceToCamera = distance(vWorldPosition, uCameraPosition);
                
                // Main grid (1.0 unit spacing) - matches Blender's default scale better
                float grid1 = getGrid(vWorldPosition.xz, 1.0);
                
                // Fine grid (0.1 unit spacing) - only visible when close
                float grid01 = getGrid(vWorldPosition.xz, 10.0);
                float fineGridFade = 1.0 - smoothstep(2.0, 8.0, distanceToCamera);
                grid01 *= fineGridFade;
                
                // Coarse grid (10 unit spacing) - more subtle, less contrast
                float grid10 = getGrid(vWorldPosition.xz, 0.1);
                
                // Combine grids with more balanced intensities - reduced contrast
                float finalGrid = grid1 * 0.4 + grid01 * 0.15 + grid10 * 0.5;
                
                // Much gentler distance-based fade - less aggressive fade-off like Blender
                float fade = 1.0 - smoothstep(200.0, 1000.0, distanceToCamera);
                finalGrid *= fade;
                
                // Axis lines (X and Z axes) - improved anti-aliasing
                float axisLineWidth = 0.015;
                float axisX = 1.0 - smoothstep(0.0, axisLineWidth, abs(vWorldPosition.z));
                float axisZ = 1.0 - smoothstep(0.0, axisLineWidth, abs(vWorldPosition.x));
                
                // Axis colors (red for X, blue for Z)
                vec3 axisColorX = vec3(0.8, 0.2, 0.2) * axisX;
                vec3 axisColorZ = vec3(0.2, 0.2, 0.8) * axisZ;
                
                // Grid color (lighter, more subtle gray like Blender)
                vec3 gridColor = vec3(0.3, 0.3, 0.3) * finalGrid;
                
                // Combine colors
                vec3 finalColor = gridColor + axisColorX + axisColorZ;
                
                // Alpha based on grid intensity and distance
                float alpha = max(finalGrid, max(axisX, axisZ)) * fade;
                
                gl_FragColor = vec4(finalColor, alpha);
            }
        `;

        // Create infinite plane geometry
        const geometry = new THREE.PlaneGeometry(100000, 100000);
        
        const material = new THREE.ShaderMaterial({
            vertexShader,
            fragmentShader,
            uniforms: {
                uTime: { value: 0 },
                uCameraPosition: { value: new THREE.Vector3() }
            },
            transparent: true,
            side: THREE.DoubleSide,
            depthWrite: false
        });

        this.infiniteGrid = new THREE.Mesh(geometry, material);
        this.infiniteGrid.rotation.x = -Math.PI / 2;
        this.infiniteGrid.position.y = 0;
        this.infiniteGrid.renderOrder = -1; // Render behind other objects
        this.scene.add(this.infiniteGrid);
        
        // Store reference to update camera position
        this.gridMaterial = material;
    }

    createOptionalGrids() {
        // Traditional grid helper (hidden by default)
        this.gridHelper = new THREE.GridHelper(20, 20, 0x3d3d3d, 0x2a2a2a);
        this.gridHelper.visible = false; // Hidden by default
        this.gridHelper.material.opacity = 0.3;
        this.gridHelper.material.transparent = true;
        this.scene.add(this.gridHelper);

        // Polar grid helper (hidden by default)
        this.polarGridHelper = new THREE.PolarGridHelper(10, 16, 8, 64, 0x3d3d3d, 0x2a2a2a);
        this.polarGridHelper.visible = false;
        this.polarGridHelper.material.opacity = 0.2;
        this.polarGridHelper.material.transparent = true;
        this.scene.add(this.polarGridHelper);
    }

    createNavigationCube() {
        // Create a navigation cube in the corner
        const cubeSize = 50;
        const geometry = new THREE.BoxGeometry(cubeSize, cubeSize, cubeSize);
        
        // Create materials for each face with labels
        const materials = [
            this.createCubeFaceMaterial('X+', 0xff4444), // Right - Red
            this.createCubeFaceMaterial('X-', 0xff4444), // Left - Red
            this.createCubeFaceMaterial('Y+', 0x44ff44), // Top - Green
            this.createCubeFaceMaterial('Y-', 0x44ff44), // Bottom - Green
            this.createCubeFaceMaterial('Z+', 0x4444ff), // Front - Blue
            this.createCubeFaceMaterial('Z-', 0x4444ff)  // Back - Blue
        ];
        
        this.navigationCube = new THREE.Mesh(geometry, materials);
        
        // Position cube in corner (will be updated in animate loop)
        this.updateNavigationCubePosition();
        
        // Add to scene
        this.scene.add(this.navigationCube);
        
        // Add click interaction
        this.setupNavigationCubeInteraction();
    }

    createCubeFaceMaterial(label, color) {
        // Create canvas for text
        const canvas = document.createElement('canvas');
        canvas.width = 128;
        canvas.height = 128;
        const context = canvas.getContext('2d');
        
        // Fill background
        context.fillStyle = `#${color.toString(16).padStart(6, '0')}`;
        context.fillRect(0, 0, 128, 128);
        
        // Add border
        context.strokeStyle = '#ffffff';
        context.lineWidth = 4;
        context.strokeRect(2, 2, 124, 124);
        
        // Add text
        context.fillStyle = '#ffffff';
        context.font = 'bold 32px Arial';
        context.textAlign = 'center';
        context.textBaseline = 'middle';
        context.fillText(label, 64, 64);
        
        // Create texture and material
        const texture = new THREE.CanvasTexture(canvas);
        return new THREE.MeshBasicMaterial({ map: texture });
    }

    updateNavigationCubePosition() {
        if (!this.navigationCube) return;
        
        // Position cube in bottom-right corner
        const canvas = this.renderer.domElement;
        const aspect = canvas.width / canvas.height;
        const distance = this.camera.position.distanceTo(new THREE.Vector3(0, 0, 0));
        
        // Calculate corner position
        const cubeDistance = Math.min(distance * 0.1, 5);
        const offsetX = cubeDistance * aspect * 0.8;
        const offsetY = -cubeDistance * 0.8;
        const offsetZ = cubeDistance * 0.3;
        
        // Position relative to camera
        const cameraDirection = new THREE.Vector3();
        this.camera.getWorldDirection(cameraDirection);
        const cameraRight = new THREE.Vector3();
        cameraRight.crossVectors(this.camera.up, cameraDirection).normalize();
        const cameraUp = this.camera.up.clone();
        
        this.navigationCube.position.copy(this.camera.position);
        this.navigationCube.position.addScaledVector(cameraRight, offsetX);
        this.navigationCube.position.addScaledVector(cameraUp, offsetY);
        this.navigationCube.position.addScaledVector(cameraDirection, offsetZ);
        
        // Rotate cube to match camera orientation
        this.navigationCube.rotation.copy(this.camera.rotation);
    }

    setupNavigationCubeInteraction() {
        // Add click detection for navigation cube faces
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        
        this.renderer.domElement.addEventListener('click', (event) => {
            // Convert mouse position to normalized device coordinates
            const rect = this.renderer.domElement.getBoundingClientRect();
            mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
            
            // Check if we clicked on the navigation cube
            raycaster.setFromCamera(mouse, this.camera);
            const intersects = raycaster.intersectObject(this.navigationCube);
            
            if (intersects.length > 0) {
                const faceIndex = intersects[0].face.materialIndex;
                this.handleNavigationCubeClick(faceIndex);
            }
        });
    }

    handleNavigationCubeClick(faceIndex) {
        const distance = this.camera.position.distanceTo(new THREE.Vector3(0, 0, 0));
        
        // Set camera positions based on face clicked
        switch (faceIndex) {
            case 0: // X+ (Right)
                this.camera.position.set(distance, 0, 0);
                break;
            case 1: // X- (Left)
                this.camera.position.set(-distance, 0, 0);
                break;
            case 2: // Y+ (Top)
                this.camera.position.set(0, distance, 0);
                break;
            case 3: // Y- (Bottom)
                this.camera.position.set(0, -distance, 0);
                break;
            case 4: // Z+ (Front)
                this.camera.position.set(0, 0, distance);
                break;
            case 5: // Z- (Back)
                this.camera.position.set(0, 0, -distance);
                break;
        }
        
        this.camera.lookAt(0, 0, 0);
        console.log(`📐 Switched to view: ${['X+', 'X-', 'Y+', 'Y-', 'Z+', 'Z-'][faceIndex]}`);
    }

    resizeRenderer() {
        const viewport = this.renderer.domElement.parentElement;
        const width = viewport.clientWidth;
        const height = viewport.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        // Update grid shader uniforms
        if (this.gridMaterial) {
            this.gridMaterial.uniforms.uCameraPosition.value.copy(this.camera.position);
            this.gridMaterial.uniforms.uTime.value += 0.01;
        }

        // Update navigation cube position
        this.updateNavigationCubePosition();

        if (this.animationEnabled && this.modelBuilder.getCurrentModel()) {
            this.modelBuilder.getCurrentModel().rotation.y += 0.01;
        }

        this.renderer.render(this.scene, this.camera);
    }

    // Control methods
    resetView() {
        // Get current model to adjust view accordingly
        const currentModel = this.modelBuilder.getCurrentModel();
        if (currentModel) {
            const box = new THREE.Box3().setFromObject(currentModel);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            const maxSize = Math.max(size.x, size.y, size.z);
            
            // Use same simple positioning logic as buildModel
            const cameraDistance = maxSize * 1.5 + 2;
            
            this.camera.position.set(
                cameraDistance * 0.7, 
                cameraDistance * 0.5, 
                cameraDistance * 0.7
            );
            this.camera.lookAt(center);
        } else {
            // Blender's default camera position
            this.camera.position.set(7.36, 4.96, 6.93);
            this.camera.lookAt(0, 0, 0);
        }
    }

    toggleWireframe() {
        this.wireframeMode = !this.wireframeMode;
        this.modelBuilder.updateWireframe(this.wireframeMode);
        return this.wireframeMode;
    }

    toggleAnimation() {
        this.animationEnabled = !this.animationEnabled;
        return this.animationEnabled;
    }

    toggleAxes() {
        this.axesVisible = !this.axesVisible;
        this.axesHelper.visible = this.axesVisible;
        return this.axesVisible;
    }

    toggleGrid() {
        this.gridVisible = !this.gridVisible;
        if (this.infiniteGrid) {
            this.infiniteGrid.visible = this.gridVisible;
        }
        return this.gridVisible;
    }

    togglePolarGrid() {
        this.polarGridVisible = !this.polarGridVisible;
        if (this.polarGridHelper) {
            this.polarGridHelper.visible = this.polarGridVisible;
        }
        return this.polarGridVisible;
    }


    buildModel(code) {
        try {
            const result = this.modelBuilder.build(code, this.scene);
            
            if (result) {
                // Much simpler and more direct camera positioning
                const maxSize = Math.max(result.size.x, result.size.y, result.size.z);
                
                // Simple, direct camera distance calculation
                const cameraDistance = maxSize * 1.5 + 2; // Much closer!
                
                // Position camera closer with a good viewing angle
                this.camera.position.set(
                    cameraDistance * 0.7, 
                    cameraDistance * 0.5, 
                    cameraDistance * 0.7
                );
                this.camera.lookAt(result.center);
                
                // Update axes helper size
                this.axesHelper.scale.setScalar(Math.max(maxSize * 0.2, 0.5));
                
                // Update grid size based on model size
                this.updateGridScale(maxSize);
                
                this.modelBuilder.updateWireframe(this.wireframeMode);
                
                console.log(`📹 Camera at distance: ${cameraDistance.toFixed(2)}, model size: ${maxSize.toFixed(2)}`);
                console.log(`📍 Camera position: (${this.camera.position.x.toFixed(2)}, ${this.camera.position.y.toFixed(2)}, ${this.camera.position.z.toFixed(2)})`);
                
                return result;
            }
        } catch (error) {
            throw error;
        }
    }

    updateGridScale(modelSize) {
        // The infinite grid automatically scales, but we can adjust the traditional grids if needed
        if (this.gridHelper) {
            // Update traditional grid size if visible
            const gridSize = Math.max(modelSize * 2, 20);
            const gridDivisions = Math.max(Math.floor(gridSize), 20);
            
            this.scene.remove(this.gridHelper);
            this.gridHelper = new THREE.GridHelper(gridSize, gridDivisions, 0x3d3d3d, 0x2a2a2a);
            this.gridHelper.visible = false; // Keep hidden by default
            this.gridHelper.material.opacity = 0.3;
            this.gridHelper.material.transparent = true;
            this.scene.add(this.gridHelper);
        }
        
        // Update polar grid as well
        if (this.polarGridHelper) {
            const gridSize = Math.max(modelSize * 2, 20);
            this.scene.remove(this.polarGridHelper);
            this.polarGridHelper = new THREE.PolarGridHelper(gridSize/2, 16, 8, 64, 0x3d3d3d, 0x2a2a2a);
            this.polarGridHelper.visible = false;
            this.polarGridHelper.material.opacity = 0.2;
            this.polarGridHelper.material.transparent = true;
            this.scene.add(this.polarGridHelper);
        }
    }

    getScene() {
        return this.scene;
    }

    getCamera() {
        return this.camera;
    }

    getRenderer() {
        return this.renderer;
    }

    loadSTL(stlData) {
        try {
            console.log('📥 Parsing STL data...');
            
            // Log data type and size for debugging
            if (stlData instanceof ArrayBuffer) {
                console.log(`📊 STL Data: ArrayBuffer, size: ${stlData.byteLength} bytes`);
            } else if (typeof stlData === 'string') {
                console.log(`📊 STL Data: String, length: ${stlData.length} characters`);
            } else {
                console.log(`📊 STL Data: Unknown type: ${typeof stlData}`);
            }
            
            // Parse STL data
            const geometry = this.parseSTL(stlData);
            
            // Create material using Blender default style
            const material = createBlenderMaterial();
            material.side = THREE.DoubleSide;  // Ensure both sides are rendered for STL
            
            // Create mesh
            const mesh = new THREE.Mesh(geometry, material);
            mesh.castShadow = true;
            mesh.receiveShadow = true;
            
            // Fix STL orientation: Convert from Z-up (CAD) to Y-up (Three.js)
            // STL models from CAD systems are typically Z-up, but Three.js uses Y-up
            mesh.rotation.x = -Math.PI / 2;  // Rotate 90 degrees around X-axis
            
            // Clear previous model
            if (this.modelBuilder.currentModel) {
                this.scene.remove(this.modelBuilder.currentModel);
            }
            
            // Add to scene
            this.scene.add(mesh);
            this.modelBuilder.currentModel = mesh;
            
            // Position camera to view the model
            const box = new THREE.Box3().setFromObject(mesh);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            const maxSize = Math.max(size.x, size.y, size.z);
            
            const cameraDistance = maxSize * 1.5 + 2;
            this.camera.position.set(
                cameraDistance * 0.7, 
                cameraDistance * 0.5, 
                cameraDistance * 0.7
            );
            this.camera.lookAt(center);
            
            console.log('✅ STL model loaded and positioned');
            return mesh;
            
        } catch (error) {
            console.error('❌ STL Loading Error:', error.message);
            // Provide more specific error information
            if (error.message.includes('offset')) {
                console.error('💡 The STL file appears to be corrupted or truncated. Please check the file integrity.');
            } else if (error.message.includes('triangle count')) {
                console.error('💡 The STL file has an invalid structure. It may be corrupted or use an unsupported format.');
            }
            throw error;
        }
    }

    parseSTL(stlData) {
        const geometry = new THREE.BufferGeometry();
        const vertices = [];
        const normals = [];
        
        // Better STL format detection
        let isAscii = false;
        
        if (typeof stlData === 'string') {
            // If it's a string and starts with 'solid', it's ASCII
            isAscii = stlData.trim().startsWith('solid');
        } else if (stlData instanceof ArrayBuffer) {
            // For ArrayBuffer, check if it starts with 'solid' when interpreted as text
            const firstBytes = new Uint8Array(stlData.slice(0, 80));
            const headerText = new TextDecoder().decode(firstBytes);
            isAscii = headerText.trim().startsWith('solid');
            
            // Additional check: ASCII STL files are usually much larger than their binary equivalent
            // Binary STL should be: 80 + 4 + (triangles * 50) bytes
            if (!isAscii && stlData.byteLength >= 84) {
                const dataView = new DataView(stlData);
                const triangleCount = dataView.getUint32(80, true);
                const expectedBinarySize = 84 + triangleCount * 50;
                
                // If the file is much larger than expected for binary, it might be ASCII
                if (stlData.byteLength > expectedBinarySize * 2) {
                    console.log('🔍 File size suggests ASCII format, double-checking...');
                    const fullText = new TextDecoder().decode(stlData);
                    isAscii = fullText.trim().startsWith('solid');
                }
            }
        }
        
        if (isAscii) {
            // Parse ASCII STL
            console.log('📝 Detected ASCII STL format');
            const textData = typeof stlData === 'string' ? stlData : new TextDecoder().decode(stlData);
            return this.parseASCIISTL(textData, geometry, vertices, normals);
        } else {
            // Parse Binary STL
            console.log('🔢 Detected Binary STL format');
            return this.parseBinarySTL(stlData, geometry);
        }
    }

    parseASCIISTL(stlData, geometry, vertices, normals) {
        // Parse ASCII STL
        const lines = stlData.split('\n');
        let currentFacet = null;
        let vertexCount = 0;
        
        for (let line of lines) {
            line = line.trim();
            
            if (line.startsWith('facet normal')) {
                const parts = line.split(' ');
                if (parts.length < 5) {
                    throw new Error(`Invalid facet normal line: ${line}`);
                }
                currentFacet = {
                    normal: [parseFloat(parts[2]), parseFloat(parts[3]), parseFloat(parts[4])],
                    vertices: []
                };
            } else if (line.startsWith('vertex')) {
                if (!currentFacet) {
                    throw new Error(`Vertex found outside of facet: ${line}`);
                }
                const parts = line.split(' ');
                if (parts.length < 4) {
                    throw new Error(`Invalid vertex line: ${line}`);
                }
                currentFacet.vertices.push([
                    parseFloat(parts[1]), 
                    parseFloat(parts[2]), 
                    parseFloat(parts[3])
                ]);
            } else if (line.startsWith('endfacet')) {
                if (!currentFacet || currentFacet.vertices.length !== 3) {
                    throw new Error(`Invalid facet: expected 3 vertices, got ${currentFacet?.vertices?.length || 0}`);
                }
                // Add triangle to geometry
                for (let vertex of currentFacet.vertices) {
                    vertices.push(vertex[0], vertex[1], vertex[2]);
                    normals.push(currentFacet.normal[0], currentFacet.normal[1], currentFacet.normal[2]);
                }
                vertexCount += 3;
                currentFacet = null;
            }
        }
        
        if (vertices.length === 0) {
            throw new Error('No valid triangles found in ASCII STL data');
        }
        
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
        geometry.computeBoundingBox();
        
        console.log(`📏 Parsed ASCII STL: ${vertexCount} vertices, ${vertexCount / 3} triangles`);
        return geometry;
    }

    parseBinarySTL(buffer, geometry) {
        // Parse Binary STL
        console.log('📥 Parsing binary STL data...');
        
        // Convert string to ArrayBuffer if needed
        let dataView;
        if (typeof buffer === 'string') {
            // Convert string to ArrayBuffer
            const encoder = new TextEncoder();
            const uint8Array = encoder.encode(buffer);
            dataView = new DataView(uint8Array.buffer);
        } else if (buffer instanceof ArrayBuffer) {
            dataView = new DataView(buffer);
        } else {
            throw new Error('Unsupported STL data format');
        }
        
        // Binary STL format:
        // 80-byte header + 4-byte triangle count + triangles
        if (dataView.byteLength < 84) {
            throw new Error('Binary STL file too small');
        }
        
        // Read triangle count (4 bytes at offset 80)
        const triangleCount = dataView.getUint32(80, true); // little endian
        console.log(`📏 Binary STL contains ${triangleCount} triangles`);
        
        // Validate triangle count
        const expectedSize = 84 + (triangleCount * 50);
        if (dataView.byteLength < expectedSize) {
            console.error(`Binary STL file size mismatch. Expected ${expectedSize} bytes, got ${dataView.byteLength} bytes`);
            throw new Error(`Binary STL file truncated or invalid triangle count. Expected ${expectedSize} bytes, got ${dataView.byteLength} bytes`);
        }
        
        // Sanity check for triangle count
        if (triangleCount > 10000000) { // 10 million triangles seems like a reasonable upper limit
            throw new Error(`Unrealistic triangle count: ${triangleCount}. File may be corrupted.`);
        }
        
        const vertices = [];
        const normals = [];
        
        // Each triangle is 50 bytes: 12 bytes normal + 36 bytes vertices + 2 bytes attribute
        for (let i = 0; i < triangleCount; i++) {
            const offset = 84 + i * 50;
            
            // Check if we have enough bytes for this triangle
            if (offset + 50 > dataView.byteLength) {
                console.warn(`Truncated STL: Only ${i} triangles read out of ${triangleCount}`);
                break;
            }
            
            try {
                // Read normal (3 floats)
                const nx = dataView.getFloat32(offset, true);
                const ny = dataView.getFloat32(offset + 4, true);
                const nz = dataView.getFloat32(offset + 8, true);
                
                // Read 3 vertices (9 floats total)
                for (let j = 0; j < 3; j++) {
                    const vertexOffset = offset + 12 + j * 12;
                    
                    // Additional bounds check for each vertex
                    if (vertexOffset + 12 > dataView.byteLength) {
                        throw new Error(`Cannot read vertex at offset ${vertexOffset}`);
                    }
                    
                    const x = dataView.getFloat32(vertexOffset, true);
                    const y = dataView.getFloat32(vertexOffset + 4, true);
                    const z = dataView.getFloat32(vertexOffset + 8, true);
                    
                    vertices.push(x, y, z);
                    normals.push(nx, ny, nz);
                }
            } catch (e) {
                console.error(`Error reading triangle ${i}: ${e.message}`);
                break;
            }
        }
        
        if (vertices.length === 0) {
            throw new Error('No valid triangles found in binary STL data');
        }
        
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
        geometry.computeBoundingBox();
        
        console.log(`📏 Parsed binary STL: ${vertices.length / 3} vertices, ${vertices.length / 9} triangles successfully read`);
        return geometry;
    }
}