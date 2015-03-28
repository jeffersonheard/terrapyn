nodes = {}

onLayerSelected = (event, node) -> window.open(node.url)
onLayerCollectionSelected = (event, node) -> window.open(node.url)
onResourceSelected = (event, node) -> window.open(node.url)
onStyleSelected = (event, node) -> window.open(node.url)
onPageSelected = (event, node) ->
  $.getJSON node.url, (n) ->
    ns = makeNodes(n)
    nodes[node.url].nodes = ns
    $("#terrapyn_page_menu").treeview data: tree

onNodeSelected = (event, node) ->
  if node.kind is "layer"
    onLayerSelected(event, node)
  else if node.kind is "collection"
    onLayerCollectionSelected(event, node)
  else if node.kind is "resource"
    onResourceSelected(event, node)
  else if node.kind is "style"
    onStyleSelected(event, node)
  else
    onPageSelected(event, node)

makePageNode = (n) -> nodes[n.url] =
  text: n.title
  url: n.url
  icon: "glyphicon glyphicon-folder-open"
  kind: "page"
  nodes: []

makeLayerNode = (n) -> nodes[n.url] =
  text: n.title
  url: n.url
  kind: "layer"
  icon: "glyphicon glyphicon-file"

makeLayerCollectionNode = (n) -> nodes[n.url] =
  text: n.title
  url: n.url
  kind: "collection"
  icon: "glyphicon glyphicon-book"

makeResourceNode = (n) -> nodes[n.url] =
  text: n.title
  url: n.url
  kind: "resource"
  icon: "glyphicon glyphicon-stats"

makeStyleNode = (n) -> nodes[n.url] =
  text: n.title
  url: n.url
  kind: "style"
  icon: "glyphicon glyphicon-pencil"

makeNodes = (n) ->
  node = makePageNode(n)
  node.nodes = (makePageNode(x) for x in n.children)
  node.nodes = node.nodes.concat (makeLayerCollectionNode(x) for x in n.layer_collections)
  node.nodes = node.nodes.concat (makeLayerNode(x) for x in n.layers)
  node.nodes = node.nodes.concat (makeStyleNode(x) for x in n.styles)
  node.nodes = node.nodes.concat (makeResourceNode(x) for x in n.data_resources)
  return node

$ ->
  $.getJSON PAGE_MENU.endpoint, (data) ->
    tree.push makeNodes(data)



