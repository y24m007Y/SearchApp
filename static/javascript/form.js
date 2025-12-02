
function click_url(query,title,rank){
    fetch("/click_url", {
        method : "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({
        query: query,
        title: title,
        rank: rank,
    })
});
}
