function togglePassword() {

    const password = document.getElementById("password");

    if (!password) return;

    if (password.type === "password") {
        password.type = "text";
    } else {
        password.type = "password";
    }

}

document.addEventListener("DOMContentLoaded", () => {

    const card = document.querySelector(".login-card");

    if (card) {

        card.animate(
            [
                {
                    opacity: 0,
                    transform: "translateY(30px)"
                },
                {
                    opacity: 1,
                    transform: "translateY(0)"
                }
            ],
            {
                duration: 600,
                easing: "ease-out",
                fill: "forwards"
            }
        );

    }

});