document.addEventListener("DOMContentLoaded", () => {

    console.log("ZYVARENTH website initialized.");

    const footerYear = document.querySelector(".footer-copy");

    if (footerYear) {
        footerYear.innerHTML =
            `© ${new Date().getFullYear()} ZYVARENTH. All rights reserved.`;
    }

});