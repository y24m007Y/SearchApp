

const cy = cytoscape({
    container: document.getElementById('cy'),
    elements:{node:nodesData, edges:edgesData},
    style: [
        {selector:nodes, style: { 'background-color':'skyblue', label:'data(id)'}},
        {selector:edges, style: { 'line-color': '#888'}, width:'data(width)'}
    ]});