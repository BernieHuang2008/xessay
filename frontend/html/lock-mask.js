/**
 * 通用锁定遮罩库 - 防止重复操作
 * 使用方法：
 * - showLockMask() 显示锁定遮罩
 * - hideLockMask() 隐藏锁定遮罩
 * - withLock(asyncFunction) 包装异步函数，自动处理锁定
 */

class LockMask {
    constructor() {
        this.isLocked = false;
        this.maskElement = null;
        this.createMaskElement();
    }

    createMaskElement() {
        // 创建遮罩元素
        this.maskElement = document.createElement('div');
        this.maskElement.id = 'global-lock-mask';
        this.maskElement.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: transparent;
            z-index: 9999;
            display: none;
            cursor: not-allowed;
        `;
        
        // 添加到页面
        document.body.appendChild(this.maskElement);
        
        // 添加点击事件，防止任何操作
        this.maskElement.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
        
        // 添加键盘事件，防止键盘操作
        this.maskElement.addEventListener('keydown', (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
        
        // 添加表单提交阻止
        this.maskElement.addEventListener('submit', (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    }

    showLock() {
        if (this.isLocked) return false; // 已经锁定
        
        this.isLocked = true;
        this.maskElement.style.display = 'block';
        
        // 禁用所有表单元素
        this.disableFormElements(true);
        
        console.log('[LockMask] 锁定已激活');
        return true;
    }

    hideLock() {
        if (!this.isLocked) return false; // 未锁定
        
        this.isLocked = false;
        this.maskElement.style.display = 'none';
        
        // 恢复所有表单元素
        this.disableFormElements(false);
        
        console.log('[LockMask] 锁定已解除');
        return true;
    }

    disableFormElements(disable) {
        // 禁用/启用所有表单元素
        const elements = document.querySelectorAll('input, button, select, textarea, a[href]');
        elements.forEach(element => {
            if (disable) {
                element.style.pointerEvents = 'none';
                element.setAttribute('data-lock-disabled', 'true');
            } else {
                element.style.pointerEvents = '';
                element.removeAttribute('data-lock-disabled');
            }
        });
    }

    // 包装异步函数，自动处理锁定
    async withLock(asyncFunction, ...args) {
        if (this.isLocked) {
            console.warn('[LockMask] 操作被阻止：系统已锁定');
            return Promise.reject(new Error('系统正在处理中，请稍候...'));
        }

        try {
            this.showLock();
            const result = await asyncFunction.apply(this, args);
            return result;
        } catch (error) {
            console.error('[LockMask] 操作执行失败:', error);
            throw error;
        } finally {
            this.hideLock();
        }
    }

    // 检查是否已锁定
    isLocked() {
        return this.isLocked;
    }

    // 强制解锁（紧急情况使用）
    forceUnlock() {
        console.warn('[LockMask] 强制解锁');
        this.hideLock();
    }
}

// 创建全局实例
const globalLockMask = new LockMask();

// 导出全局函数
window.showLockMask = () => globalLockMask.showLock();
window.hideLockMask = () => globalLockMask.hideLock();
window.withLock = (fn, ...args) => globalLockMask.withLock(fn, ...args);
window.isSystemLocked = () => globalLockMask.isLocked();
window.forceUnlock = () => globalLockMask.forceUnlock();

// 页面卸载时自动解锁
window.addEventListener('beforeunload', () => {
    globalLockMask.forceUnlock();
});

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('[LockMask] 锁定遮罩库已初始化');
});

// 导出类供高级用法
window.LockMask = LockMask;