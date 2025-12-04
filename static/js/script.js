document.addEventListener("DOMContentLoaded", function () {
    const confirmButtons = document.querySelectorAll(".confirm-action");
    const modalElement = document.getElementById("confirmModal");
    const confirmModal = new bootstrap.Modal(modalElement);
    const modalConfirmBtn = document.getElementById("modal-confirm-btn");
    const modalBodyText = document.getElementById("modal-body-text");

    let targetHref = "#";

    confirmButtons.forEach(btn => {
        btn.addEventListener("click", function (e) {
            e.preventDefault();
            targetHref = this.getAttribute("href");

            modalBodyText.textContent = this.textContent.includes("Logout")
                ? "Are you sure you want to logout?"
                : "Are you sure you want to delete this entry?";

            confirmModal.show();
        });
    });

    modalConfirmBtn.addEventListener("click", function () {
        confirmModal.hide();
        setTimeout(() => {
            window.location.href = targetHref;
        }, 200); // ensures modal fully hides before redirect
    });
});