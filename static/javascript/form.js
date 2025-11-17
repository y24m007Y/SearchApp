document.getElementById("adding_tag").addEventListener("submit", async function(e) {
    e.preventDefault();

    const formdata = new FormData(this);
    const response = await fetch("/tag_links",{
        method: "POST",
        body: formdata
    });

    if (response.ok)
    {
        alert("タグを追加しました。");
    }
    else
    {
        alert("エラーが発生しました。");
    }
});
