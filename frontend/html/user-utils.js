// 用户管理工具函数

// 获取或设置用户名
function getCurrentUser() {
    let username = localStorage.getItem('username');
    if (!username) {
        username = prompt('请输入您的用户名：');
        if (username && username.trim()) {
            localStorage.setItem('username', username.trim());
            return username.trim();
        } else {
            username = 'guest_' + Date.now();
            localStorage.setItem('username', username);
            return username;
        }
    }
    return username;
}

// 设置用户名
function setCurrentUser(username) {
    if (username && username.trim()) {
        localStorage.setItem('username', username.trim());
        return username.trim();
    }
    return null;
}

// 清除用户名
function clearCurrentUser() {
    localStorage.removeItem('username');
}

// 获取URL参数
function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    const regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    const results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

// 导航到主页
function navigateToHome() {
    window.location.href = 'index.html';
}

// 导航到带session的主页
function navigateToHomeWithSession(sessionId) {
    window.location.href = `index.html?sessionid=${sessionId}`;
}

// 添加返回按钮到页面
function addBackButton(containerId = 'backButtonContainer') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <button onclick="navigateToHome()" style="background: #667eea; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; margin-right: 10px;">
                ← 返回主页
            </button>
        `;
    }
}