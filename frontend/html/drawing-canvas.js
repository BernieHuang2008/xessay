// 绘图组件类
class DrawingCanvas {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            backgroundColor: '#ffffff',
            penColor: '#000000',
            penSize: 2,
            eraserSize: 10,
            maxUndoSteps: 20,
            ...options
        };
        
        this.canvas = null;
        this.ctx = null;
        this.isDrawing = false;
        this.currentTool = 'pen'; // pen, eraser
        this.undoStack = [];
        this.currentPath = [];
        this.isToolbarCollapsed = false;
        this.toolbar = null;
        
        this.init();
    }

    init() {
        this.createCanvas();
        this.createToolbar();
        this.attachEvents();
        this.saveState();
    }

    createCanvas() {
        // 创建canvas容器
        const canvasContainer = document.createElement('div');
        canvasContainer.className = 'drawing-area';
        canvasContainer.style.cssText = `
            position: relative;
            width: 100%;
            height: 100%;
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
            background: ${this.options.backgroundColor};
        `;

        // 创建canvas元素
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.canvas.style.cssText = `
            display: block;
            cursor: crosshair;
        `;

        // 设置canvas尺寸
        this.resizeCanvas();
        
        canvasContainer.appendChild(this.canvas);
        this.container.appendChild(canvasContainer);
        
        // 监听窗口大小变化
        window.addEventListener('resize', () => this.resizeCanvas());
    }

    createToolbar() {
        this.toolbar = document.createElement('div');
        this.toolbar.className = 'drawing-toolbar';
        this.toolbar.style.cssText = `
            position: fixed;
            left: 10px;
            top: 50%;
            transform: translateY(-50%);
            display: flex;
            flex-direction: column;
            gap: 10px;
            background: rgba(255, 255, 255, 0.9);
            padding: 15px 10px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            z-index: 10;
            transition: all 0.3s ease;
        `;

        // Create collapse/expand button
        const collapseBtn = document.createElement('button');
        collapseBtn.className = 'collapse-btn';
        collapseBtn.innerHTML = '◀';
        collapseBtn.title = '折叠工具栏';
        collapseBtn.style.cssText = `
            position: absolute;
            right: -30px;
            top: 10px;
            width: 25px;
            height: 25px;
            border: none;
            border-radius: 50%;
            background: rgba(102, 126, 234, 0.8);
            color: white;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        collapseBtn.addEventListener('click', () => this.toggleToolbar());
        this.toolbar.appendChild(collapseBtn);

        // Create tools container
        const toolsContainer = document.createElement('div');
        toolsContainer.className = 'tools-container';
        toolsContainer.style.cssText = `
            display: flex;
            flex-direction: column;
            gap: 10px;
            transition: all 0.3s ease;
        `;

        const tools = [
            { name: 'pen', icon: '✏️', title: '画笔' },
            { name: 'eraser', icon: '🧹', title: '橡皮擦' },
            { name: 'undo', icon: '↶', title: '撤销' },
            { name: 'pageUp', icon: '⬆️', title: '向上翻页' },
            { name: 'pageDown', icon: '⬇️', title: '向下翻页' },
            { name: 'clear', icon: '🗑️', title: '清空' }
        ];

        tools.forEach(tool => {
            const button = document.createElement('button');
            button.className = 'tool-btn';
            button.innerHTML = tool.icon;
            button.title = tool.title;
            button.style.cssText = `
                width: 40px;
                height: 40px;
                border: none;
                border-radius: 8px;
                background: ${tool.name === this.currentTool ? '#667eea' : '#f5f5f5'};
                color: ${tool.name === this.currentTool ? 'white' : '#333'};
                font-size: 16px;
                cursor: pointer;
                transition: all 0.2s ease;
            `;

            button.addEventListener('click', () => this.handleToolClick(tool.name, button));
            button.addEventListener('mouseenter', () => {
                if (tool.name !== this.currentTool) {
                    button.style.background = '#e0e0e0';
                }
            });
            button.addEventListener('mouseleave', () => {
                if (tool.name !== this.currentTool) {
                    button.style.background = '#f5f5f5';
                }
            });

            toolsContainer.appendChild(button);
        });

        // 画笔大小控制
        const sizeControl = document.createElement('div');
        sizeControl.style.cssText = `
            display: flex;
            flex-direction: column;
            gap: 5px;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
        `;

        const sizeLabel = document.createElement('label');
        sizeLabel.textContent = '粗细';
        sizeLabel.style.cssText = `
            font-size: 12px;
            color: #666;
            text-align: center;
        `;

        const sizeSlider = document.createElement('input');
        sizeSlider.type = 'range';
        sizeSlider.min = '1';
        sizeSlider.max = '20';
        sizeSlider.value = this.options.penSize;
        sizeSlider.style.cssText = `
            width: 60px;
            height: 20px;
        `;

        sizeSlider.addEventListener('input', (e) => {
            this.options.penSize = parseInt(e.target.value);
        });

        sizeControl.appendChild(sizeLabel);
        sizeControl.appendChild(sizeSlider);
        toolsContainer.appendChild(sizeControl);
        
        this.toolbar.appendChild(toolsContainer);
        this.container.querySelector('.drawing-area').appendChild(this.toolbar);
    }

    resizeCanvas() {
        const container = this.container;
        // console.log(this.container);
        const rect = container.getBoundingClientRect();
        
        // 保存当前绘制内容
        const imageData = this.ctx ? this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height) : null;
        
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
        
        // 恢复绘制内容
        if (imageData) {
            this.ctx.putImageData(imageData, 0, 0);
        }
        
        // 重新设置canvas样式
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
    }

    attachEvents() {
        // 鼠标事件
        this.canvas.addEventListener('mousedown', (e) => this.startDrawing(e));
        this.canvas.addEventListener('mousemove', (e) => this.draw(e));
        this.canvas.addEventListener('mouseup', () => this.stopDrawing());
        this.canvas.addEventListener('mouseout', () => this.stopDrawing());

        // 触摸事件
        this.canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.startDrawing(e.touches[0]);
        });
        this.canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            this.draw(e.touches[0]);
        });
        this.canvas.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.stopDrawing();
        });
    }

    getCoordinates(e) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }

    startDrawing(e) {
        this.isDrawing = true;
        const coords = this.getCoordinates(e);
        this.currentPath = [coords];
        
        this.ctx.beginPath();
        this.ctx.moveTo(coords.x, coords.y);
        
        if (this.currentTool === 'pen') {
            this.ctx.globalCompositeOperation = 'source-over';
            this.ctx.strokeStyle = this.options.penColor;
            this.ctx.lineWidth = this.options.penSize;
        } else if (this.currentTool === 'eraser') {
            this.ctx.globalCompositeOperation = 'destination-out';
            this.ctx.lineWidth = this.options.eraserSize;
        }
    }

    draw(e) {
        if (!this.isDrawing) return;
        
        const coords = this.getCoordinates(e);
        this.currentPath.push(coords);
        
        this.ctx.lineTo(coords.x, coords.y);
        this.ctx.stroke();
    }

    stopDrawing() {
        if (this.isDrawing) {
            this.isDrawing = false;
            this.saveState();
        }
    }

    handleToolClick(toolName, button) {
        switch (toolName) {
            case 'pen':
            case 'eraser':
                this.setTool(toolName);
                break;
            case 'undo':
                this.undo();
                break;
            case 'pageUp':
                this.pageUp();
                break;
            case 'pageDown':
                this.pageDown();
                break;
            case 'clear':
                this.clear();
                break;
        }
        
        this.updateToolButtons();
    }

    setTool(toolName) {
        this.currentTool = toolName;
        this.canvas.style.cursor = toolName === 'pen' ? 'crosshair' : 'grab';
    }

    updateToolButtons() {
        const buttons = this.container.querySelectorAll('.tool-btn');
        buttons.forEach((btn, index) => {
            const tools = ['pen', 'eraser', 'undo', 'pageUp', 'pageDown', 'clear'];
            const isActive = tools[index] === this.currentTool;
            btn.style.background = isActive ? '#667eea' : '#f5f5f5';
            btn.style.color = isActive ? 'white' : '#333';
        });
    }

    saveState() {
        this.undoStack.push(this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height));
        if (this.undoStack.length > this.options.maxUndoSteps) {
            this.undoStack.shift();
        }
    }

    undo() {
        if (this.undoStack.length > 1) {
            this.undoStack.pop(); // 移除当前状态
            const prevState = this.undoStack[this.undoStack.length - 1];
            this.ctx.putImageData(prevState, 0, 0);
        }
    }

    toggleToolbar() {
        const toolsContainer = this.toolbar.querySelector('.tools-container');
        const collapseBtn = this.toolbar.querySelector('.collapse-btn');
        
        if (this.isToolbarCollapsed) {
            // Expand toolbar
            toolsContainer.style.opacity = '1';
            toolsContainer.style.pointerEvents = 'auto';
            toolsContainer.style.maxHeight = '500px';
            this.toolbar.style.padding = '15px 10px';
            collapseBtn.innerHTML = '◀';
            collapseBtn.title = '折叠工具栏';
        } else {
            // Collapse toolbar
            toolsContainer.style.opacity = '0';
            toolsContainer.style.pointerEvents = 'none';
            toolsContainer.style.maxHeight = '0';
            this.toolbar.style.padding = '0';
            collapseBtn.innerHTML = '▶';
            collapseBtn.title = '展开工具栏';
        }
        
        this.isToolbarCollapsed = !this.isToolbarCollapsed;
    }

    pageUp() {
        // Try to scroll the document first
        const scrollableElement = this.findScrollableParent();
        const currentScroll = scrollableElement === document.documentElement ? 
            window.pageYOffset || document.documentElement.scrollTop : 
            scrollableElement.scrollTop;
        
        if (currentScroll > 0) {
            // Scroll up by 50% of viewport height
            const scrollAmount = Math.min(currentScroll, window.innerHeight * 0.5);
            if (scrollableElement === document.documentElement) {
                window.scrollBy(0, -scrollAmount);
            } else {
                scrollableElement.scrollTop -= scrollAmount;
            }
        }
        // If already at top, do nothing (don't modify canvas)
    }

    pageDown() {
        // Try to scroll the document first
        const scrollableElement = this.findScrollableParent();
        const maxScroll = scrollableElement === document.documentElement ? 
            document.documentElement.scrollHeight - window.innerHeight :
            scrollableElement.scrollHeight - scrollableElement.clientHeight;
        const currentScroll = scrollableElement === document.documentElement ? 
            window.pageYOffset || document.documentElement.scrollTop : 
            scrollableElement.scrollTop;

        if (currentScroll < maxScroll-10) {
            // Scroll down by 50% of viewport height
            const scrollAmount = Math.min(maxScroll - currentScroll, window.innerHeight * 0.5);
            if (scrollableElement === document.documentElement) {
                window.scrollBy(0, scrollAmount);
            } else {
                scrollableElement.scrollTop += scrollAmount;
            }
        } else {
            // At bottom, expand the canvas area
            const container = this.container.querySelector('.drawing-area');
            const currentHeight = container.offsetHeight;
            const newHeight = currentHeight * 1.5; // 增加50%高度
            
            container.style.height = newHeight + 'px';
            this.resizeCanvas();
            
            // Scroll to the newly added area
            setTimeout(() => {
                if (scrollableElement === document.documentElement) {
                    window.scrollBy(0, window.innerHeight * 0.5);
                } else {
                    scrollableElement.scrollTop += scrollableElement.clientHeight * 0.5;
                }
            }, 100);
        }
    }

    findScrollableParent() {
        let element = this.container;
        while (element && element !== document.documentElement) {
            const overflow = window.getComputedStyle(element).overflow;
            if (overflow === 'auto' || overflow === 'scroll') {
                return element;
            }
            element = element.parentElement;
        }
        return document.documentElement;
    }

    clear() {
        if (confirm('确定要清空画布吗？')) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            this.ctx.fillStyle = this.options.backgroundColor;
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            this.saveState();
        }
    }

    // 导出为图片
    toBlob(callback, type = 'image/png', quality = 0.8) {
        // 创建临时画布以确保白色背景
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        
        tempCanvas.width = this.canvas.width;
        tempCanvas.height = this.canvas.height;
        
        // 填充白色背景
        tempCtx.fillStyle = '#ffffff';
        tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
        
        // 绘制原始画布内容到临时画布上
        tempCtx.drawImage(this.canvas, 0, 0);
        
        // 从临时画布导出
        tempCanvas.toBlob(callback, type, quality);
    }

    // 导出为DataURL
    toDataURL(type = 'image/png', quality = 0.8) {
        // 创建临时画布以确保白色背景
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        
        tempCanvas.width = this.canvas.width;
        tempCanvas.height = this.canvas.height;
        
        // 填充白色背景
        tempCtx.fillStyle = '#ffffff';
        tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
        
        // 绘制原始画布内容到临时画布上
        tempCtx.drawImage(this.canvas, 0, 0);
        
        // 从临时画布导出
        return tempCanvas.toDataURL(type, quality);
    }

    // 设置画布尺寸
    setSize(width, height) {
        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        this.canvas.width = width;
        this.canvas.height = height;
        this.ctx.putImageData(imageData, 0, 0);
    }
}

// 导出类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DrawingCanvas;
} else {
    window.DrawingCanvas = DrawingCanvas;
}