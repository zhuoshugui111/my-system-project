// 超市财务管理系统自定义脚本

// 删除确认功能
function confirmDelete() {
    return confirm('确定要删除这条记录吗？此操作不可恢复。');
}

// 表单提交前的简单验证
function validateForm() {
    // 可以在这里添加表单验证逻辑
    return true;
}

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 添加删除确认事件监听器到所有带有delete-btn类的按钮
    const deleteButtons = document.querySelectorAll('.delete-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirmDelete()) {
                e.preventDefault();
            }
        });
    });
});
