
function click_url(title,rank){
    fetch("/click_url", {
        method : "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({
        title: title,
        rank: rank,
        time: Date.now()
    })
});
}
