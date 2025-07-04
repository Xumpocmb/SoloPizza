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