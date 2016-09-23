
// Width and height
var w = 500;
var h = 300;

var projection = d3.geo.albersUsa()
    .translate([w/2, h/2])
    .scale([500]);

var path = d3.geo.path()
    .projection(projection);

var color = d3.scale.quantize()
    .range(["rgb(237,248,233)","rgb(186,228,179)","rgb(116,196,118)","rgb(49,163,84)","rgb(0,109,44)"]);

// Create SVG element
var svg = d3.select("body")
    .append("svg")
    .attr("width", w)
    .attr("height", h);

var dataset = {"University":{"0":"Cornell","1":"Berkeley","2":"Harvard","3":"Massachusetts Institute of Technology"},"Domain":{"0":"Vision","1":"Vision","2":"Molecular Bio.","3":"Molecular Bio."},"Funding":{"0":100,"1":10000,"2":1000000,"3":10000},"PI":{"0":"Joe","1":"Sarah","2":"Adam","3":"Lucy"},"Full_Address":{"0":"Cornell College, 600 First St. SW, Mount Vernon, Iowa, 52314-1098","1":"University of California - Berkeley, 200 California Hall, Berkeley, California, 94720","2":"Harvard University, Massachusetts Hall, Cambridge, Massachusetts, 02138","3":"Massachusetts Institute of Technology, 77 Massachusetts Avenue, Cambridge, Massachusetts, 02139-4307"},"lat_lng":{"0":[41.9245718,-91.4237652],"1":[37.866354,-122.310242],"2":[42.3744368,-71.118281],"3":[42.3647559,-71.1032591]}}

//var dataset = d3.csv("to_vis_data.csv")


d3.json("us-states.json", function(json) {

    svg.selectAll("path")
        .data(json.features)
        .enter()
        .append("path")
        .attr("d", path)
        .style("fill", "steelblue");

});






















































