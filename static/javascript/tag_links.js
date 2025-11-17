

/*const cy = cytoscape({
    container: document.getElementById('cy'),
    elements:{node:nodesData, edges:edgesData},
    style: [
        {selector:nodes, style: { 'background-color':'skyblue', label:'data(id)'}},
        {selector:edges, style: { 'line-color': '#888'}, width:'data(width)'}
    ]});*/
    
window.addEventListener('DOMContentLoaded', () => {
  if (typeof nodesData !== 'undefined' && typeof edgesData !== 'undefined') {
    const cy = cytoscape({
      container: document.getElementById('cy'),
      elements: {
        nodes: nodesData,
        edges: edgesData
      },
      style: [
        { selector: 'node', style: { 'background-color': 'data(color)', 'label': 'data(id)', 'font-size':'8'}},
        { selector: 'edge', style: { 'line-color': '#888', 'width': 'data(width)' }}
      ],
      layout: { name: 'cose'}
    });
      cy.on('tap', 'node', function(evt) {
      const node = evt.target;
      const word = node.data('id');
      document.getElementById("explain_tag").textContent = word;
      document.getElementById("hidden_add_tag").textContet = word;
      fetch('/tag_explain', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ word: word })
        })
        .then(res => res.json())
        .then(data => {
        document.getElementById("explain").textContent = data.explain;
      });
    });
  }
});



