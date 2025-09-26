const checkboxes = document.querySelectorAll("input[name=tag]");
checkboxes.forEach(cb =>{
    cb.addEventListener("change", () => {
        const selected = Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value);
        document.getElementById("option-tags").textContent = "選択タグ:" + selected.join(", ");
    }); 
});
