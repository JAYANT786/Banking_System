/* ============================= */
/* GLOBAL INIT */
/* ============================= */

document.addEventListener("DOMContentLoaded", function () {

    const spinner = document.getElementById("loading-spinner");
    const sound = document.getElementById("success-sound");

    /* ============================= */
    /* SHOW SPINNER ON ALL FORMS */
    /* ============================= */

    const forms = document.querySelectorAll("form");

    forms.forEach(form => {
        form.addEventListener("submit", function () {

            if (spinner) {
                spinner.style.display = "flex";
            }

            if (sound) {
                sound.currentTime = 0;
                sound.play();
            }

        });
    });

    /* ============================= */
    /* AUTO HIDE ALERT MESSAGES */
    /* ============================= */

    setTimeout(() => {
        document.querySelectorAll(".auto-hide").forEach(msg => {
            msg.style.display = "none";
        });
    }, 4000);

    /* ============================= */
    /* QUICK AMOUNT BUTTONS */
    /* ============================= */

    function setAmount(buttonClass, inputSelector) {
        document.querySelectorAll(buttonClass).forEach(btn => {
            btn.addEventListener("click", function () {
                const amount = this.innerText.replace("₹", "");
                const input = document.querySelector(inputSelector);

                if (input) {
                    input.value = amount;
                }
            });
        });
    }

    setAmount(".quick-amt", "input[name='amount']");
    setAmount(".quick-transfer", "input[name='amount']");
    setAmount(".quick-withdraw", "input[name='amount']");

    /* ============================= */
    /* OTP HANDLING */
    /* ============================= */

    const otpInputs = document.querySelectorAll(".otp-box");

    if (otpInputs.length > 0) {

        const hiddenInput = document.getElementById("otp-full");

        otpInputs.forEach((input, index) => {

            input.addEventListener("keyup", function (e) {

                // Move forward
                if (this.value.length === 1 && index < otpInputs.length - 1) {
                    otpInputs[index + 1].focus();
                }

                // Move backward
                if (e.key === "Backspace" && index > 0) {
                    otpInputs[index - 1].focus();
                }

                // Combine OTP
                let otp = "";
                otpInputs.forEach(i => otp += i.value);

                if (hiddenInput) {
                    hiddenInput.value = otp;
                }

                // Auto submit when 6 digits entered
                if (otp.length === 6 && hiddenInput) {
                    hiddenInput.form.submit();
                }

            });

        });
    }

    /* ============================= */
    /* LOADING SPINNER HIDE (AFTER LOAD) */
    /* ============================= */

    window.addEventListener("load", function () {
        if (spinner) {
            spinner.style.display = "none";
        }
    });

});

document.addEventListener("DOMContentLoaded", function () {

    const links = document.querySelectorAll(".nav-item");

    links.forEach(link => {
        if (link.href === window.location.href) {
            link.classList.add("active");
        }
    });

});