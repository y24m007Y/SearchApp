

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
        { selector: 'node', style: { 'background-color': 'data(color)', 'label': 'data(id)', 'width':'mapData(data(count),1,300,20,60)', 'height':'mapData(data(count),1,300,20,60)'}},
        { selector: 'edge', style: { 'line-color': '#888', 'width': 'data(width)' }}
      ],
      layout: { name: 'cose' }
    });
  }
});
