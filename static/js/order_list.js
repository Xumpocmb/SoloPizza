document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.cancel-order-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('Вы уверены, что хотите отменить этот заказ?')) {
                e.preventDefault();
            }
        });
    });

    // Быстрое применение фильтра при изменении селекта
    const statusFilter = document.querySelector('.status-filter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            this.closest('form').submit();
        });
    }
});

// Функция для переключения отображения селектора филиалов
function toggleBranchSelector() {
    const branchSelector = document.getElementById('branchSelector');
    if (branchSelector) {
        if (branchSelector.style.display === 'none') {
            branchSelector.style.display = 'block';
        } else {
            branchSelector.style.display = 'none';
        }
    }
}

// Функция для переключения отображения селектора филиала для конкретного заказа
function toggleOrderBranchSelector(selectorId) {
    const branchSelector = document.getElementById(selectorId);
    if (branchSelector) {
        if (branchSelector.style.display === 'none') {
            branchSelector.style.display = 'block';
        } else {
            branchSelector.style.display = 'none';
        }
    }
}