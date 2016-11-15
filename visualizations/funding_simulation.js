/**
 * Map of Global Science Funding.
 * Tariq A. Hassan, 2016.
 */

//----------------------------------------------------------------------------------------//

// Key Resources Used for Help:
//      1. http://techslides.com/d3-map-starter-kit
//      2. http://www.tnoda.com/blog/2014-04-02

//----------------------------------------------------------------------------------------//

//General Setup

d3.select(window).on("resize", throttle);

var zoom = d3.behavior.zoom()
                      .scaleExtent([1, 5000])
                      .on("zoom", zoomer);

// var width = document.getElementById("container").offsetWidth;
// var height = width / 2;

var margin = {top: 0, right: 0, bottom: 0, left: 0},
    width  = document.getElementById("container").offsetWidth + 500 - margin.left - margin.right,
    height = document.getElementById("container").offsetWidth/2 + margin.bottom;

// Define the div for the tooltip
var div = d3.select("body").append("div")
                           .attr("class", "tooltip")
                           .style("opacity", 0);

//----------------------------------------------------------------------------------------//

//Initialize

//Variables and Constants
var topo, projection, path, defs, filter, feMerge, text, legend, svgLwr, gLwr, svg, funderLayer, g;
var currentYear = "";
var legendBoxHeight = 240;
var largestSingleGrant = 0;
var largestTotalGrantByOrg = 0;

//Arrays
var dateRealTime = [];
var fundersPresentInDB = [];

//Objects
var funderColors = {};
var funderGeoDict = {};
var funderYearByYear = {};
var recipientRankings = {};
var abbreviationFunderName = {};
var funderNameAbbreviation = {};
var funderColorsAbbreviation = {};
var fundingAgencyFlightStatus = {};

//----------------------------------------------------------------------------------------//

setup(width, height);
function setup(width, height){
    dateRealTime = [];

    projection = d3.geo.mercator()
                       .translate([(width/1.55), (height/0.95)])
                       .scale(width / 1.30 / Math.PI);

    path = d3.geo.path().projection(projection);

    svg = d3.select("#container")
            .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height)
            .call(zoom)
            .append("g");

    //General Layer
    g = svg.append("g");

    //Layer on top for the Funding Agency Markers
    funderLayer = svg.append("g");

    svgLwr = d3.select("#container2")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", legendBoxHeight)
        .append("g");

    gLwr = svgLwr.append("g");

    //---------------------
    //Add Glow
    //See:
    //      1. http://www.visualcinnamon.com/2016/06/glow-filter-d3-visualization.html
    //      2. http://stackoverflow.com/a/19704735/4898004

    //Container for the gradients
    defs = svgLwr.append("defs");

    //Filter for the outside glow
    filter = defs.append("filter")
                    .attr("id","glow");

    filter.append("feGaussianBlur")
                    .attr("stdDeviation","5.5")
                    .attr("result","coloredBlur");

    feMerge = filter.append("feMerge");

    feMerge.append("feMergeNode")
                    .attr("in","coloredBlur");

    feMerge.append("feMergeNode")
                    .attr("in","SourceGraphic");
}

//----------------------------------------------------------------------------------------//

//Tooltip Functionality

var tooltipContainer = d3.select("#container")
                            .append("div")
                            .attr("class", "tooltip hidden");

var tooltipContainer2 = d3.select("#container2")
                            .append("div")
                            .attr("class", "tooltip hidden");

function showTooltip(d, tooltipObj, info, offsetL, offsetT){
    var mouse = d3.mouse(svg.node()).map(function(d) {
        return parseInt(d);
    });
    tooltipObj.classed("hidden", false)
        .attr("style", "left:"+(mouse[0]-offsetL)+"px;" +
                        "top:"+(mouse[1]+offsetT)+"px"
        )
        .html(info)
        .style("font-size", "45px");
}

function hideTooltip(tooltipObj){
     tooltipObj.classed("hidden", true);
}

//----------------------------------------------------------------------------------------//

//DateBox

//Pass the starting date
function addDate(startDate) {
    var xWidthAdjust = 50;
    var startingContainerWidth = document.getElementById("container").offsetWidth;

    text = svg.append("text")
                .attr("class", "datebox")
                .attr("x", startingContainerWidth - 300)
                .attr("y", (startingContainerWidth / 2) - 80)
                .attr("dy", ".35em")
                .attr("text-anchor", "middle")
                .style("font", "Lucida Grande")
                .style("font-size", "85px")
                .style("opacity", 0)
                .text(startDate);

    var bbox = text[0][0].getBBox();

    svg.insert("rect", "text")
        .attr("class", "datebox")
        .attr("x", bbox.x - xWidthAdjust/2)
        .attr("y", bbox.y)
        .attr("width", bbox.width + xWidthAdjust)
        .attr("height", bbox.height)
        .style("fill", "white")
        .style("opacity", 0.35);

    svg.append("text")
        .attr("class", "datebox")
        .attr("x", startingContainerWidth - 300)
        .attr("y", (startingContainerWidth / 2) - 80)
        .attr("dy", ".35em")
        .attr("text-anchor", "middle")
        .style("font", "Lucida Grande")
        .style("opacity", 1)
        .style("font-size", "85px")
        .text(startDate);
}

function dateChecker(newDate, oldDate) {
    //Checks if "newDate" is more recent
    //than "oldDate". If so, returns `true`.
    //Otherwise, returns `false`.
    //Format: DD-MM-YYYY.
    var oldSplit = oldDate.split("/").map(parseFloat);
    var newSplit = newDate.split("/").map(parseFloat);

    if (newSplit[2] > oldSplit[2]) {
        return true;
    } else if (newSplit[1] > oldSplit[1]) {
        return true;
    } else if (newSplit[0] > oldSplit[0]) {
        return true;
    }
    return false;
}

//----------------------------------------------------------------------------------------//

//Tooltip Funders Summary

function uniqueCountPreserve(inputList) {
    //See: http://stackoverflow.com/a/22011372/4898004
    //This is a very nice little algorithm for sorting
    //array elements by the number of their occurrences
    //Returns an array of uniques.
    var map = inputList.reduce(function (p, c) {
        p[c] = (p[c] || 0) + 1;
        return p;
    }, {});
    var countArray = Object.keys(map).sort(function (a, b) {
        return map[a] < map[b];
    });
    return countArray
}

function orgListFormatter(orgList){
    var d = {};
    var tail = "";
    var uniqueOrgList = uniqueCountPreserve(orgList);
    var uniqueOrgListLast = uniqueOrgList[uniqueOrgList.length - 1];

    for (var i in orgList) {
        if (d[orgList[i]] === undefined) {
            d[orgList[i]] = 1
        } else {
            d[orgList[i]] += 1
        }
    }

    var summaryString = "";
    var insetBreakSpent = false;
    for (i in uniqueOrgList){
        if (uniqueOrgList[i] === uniqueOrgListLast) {
            tail = ")";
        } else if ((i == 2) && (insetBreakSpent === false)){
            tail = ")" + "</br>";
            insetBreakSpent = true;
        } else {
            tail = "), ";
        }
        summaryString += uniqueOrgList[i] + " (" + d[uniqueOrgList[i]] + tail;
    }
    return summaryString;
}

function tooltipInfoFormater(destination, realTimeInfo, locID){
    var info = "<strong>" + destination + "</strong>" + " (#" + recipientRankings[destination] + ")" +"<br/>" +
                "<em>" + "Total Grants: " + "</em>" + accounting.formatMoney(parseFloat(realTimeInfo[locID][0])) +
                " USD" + "<br/>" + "<em>" + "Grants Awarded by: " + orgListFormatter(realTimeInfo[locID][1]) + "</em>"
    return info;
}

//----------------------------------------------------------------------------------------//

//Circle Scaling

function logistic_fn(x, minValue, maxValue, k, c){
    // Algorithm to scale points using a Logistic Function.
    // See: https://en.wikipedia.org/wiki/Logistic_function
    // Notes:
    //     (a) x *must* be >= 0.
    //     (b) x_0 is left as 0 to center the function about x = 0.
    //     (c) "-L/2" was added to center the function about y = 0.
    //     (d) curveSteepness (k) should be set to be ~= 1.
    // maxAmount (Order of Magnitude) / 10
    var maxOrderOfMag = Math.pow(10, parseInt(Math.log10(maxValue)) - 1);
    var scaleBy = maxOrderOfMag * c;

    var L = maxValue/scaleBy;
    var denominator = 1 + Math.pow(Math.E, -1 * k * (x/scaleBy));

    return L/denominator - L/2 + minValue
}

//----------------------------------------------------------------------------------------//

//Dot Movement Machinery

function delta(grantMovement, path) {
    var l = path.getTotalLength();
    var grantMovement = grantMovement;
    return function(i) {
        return function(t) {
            var p = path.getPointAtLength(t * l);

            var t2 = Math.min(t + 0.05, 1);
            var p2 = path.getPointAtLength(t2 * l);

            var x = p2.x - p.x;
            var y = p2.y - p.y;

            var s = Math.min(Math.sin(Math.PI * t) * 0.7, 0.3);

            //correct for the current zoom level.
            var sZoom = pointScale(s, zoom.scale());

            return "translate(" + p.x + "," + p.y + ") scale(" + sZoom + ")";
        }
    }
}

function terrestrialPoints(newDraw, grantToDraw, realTimeInfo){
    //Model Params
    var c = 0.65;
    var k = 0.1;
    var sizeFloor = 1.5;

    //Get the current zoom level
    var s = zoom.scale();

    //Set unique ID and the name of final location
    var locID = grantToDraw["recipientUniqueGeo"];
    var destination = grantToDraw["grantRecipientOrg"];

    //Construct the info for the Point

    // var s = d3.event.scale; //Add to adjust radius based on current zoom
    var idClean = "loc" + locID.replace(/[^0-9a-z]/gi, "");

    //Scale the funding using the logistic function
    var scaledRadius = logistic_fn(x = realTimeInfo[locID][0], sizeFloor, largestTotalGrantByOrg, k, c);
    // if (scaledRadius < sizeFloor){scaledRadius += sizeFloor}

    //Get the Agency that has given the most to the current institution
    var largestContributorColor = funderColorsAbbreviation[uniqueCountPreserve(realTimeInfo[locID][1])[0]];

    if (newDraw === true) {
        var institution = g.append("g").attr("class", "institution");
        var location = projection(funderGeoDict[destination]);
        institution = g.append("g").attr("class", "institution");
        institution.append("svg:circle")
                    .attr("cx", location[0])
                    .attr("cy", location[1])
                    .attr("class", "institution")
                    .attr("id", idClean)
                    .attr("r", pointScale(scaledRadius, s))
                    .datum(scaledRadius)
                    .style("fill", largestContributorColor)
                    .style("opacity", 0.45)
                    .on("mousemove", function(d) {
                        showTooltip(d
                                    , tooltipContainer
                                    , tooltipInfoFormater(destination, realTimeInfo, locID)
                                    , document.getElementById("container").offsetLeft-20
                                    , document.getElementById("container").offsetTop+20
                    )})
                    .on("mouseout",  function() {
                        hideTooltip(tooltipContainer)
                    });
    } else {
        d3.selectAll(".institution")
            .select("#" + idClean)
            .attr("r", pointScale(scaledRadius, s))
            .style("fill", largestContributorColor)
            .datum(scaledRadius);
    }
}

function legendCircleActivityScaler(grantToDraw){
        var status = fundingAgencyFlightStatus[grantToDraw["funderName"]];

        if (status == 0){
            var transitionRate = 450;
        } else {
            var transitionRate = 300;
        }

        d3.selectAll("#container2")
            .select("#" + grantToDraw["funderName"].match(/\((.*?)\)/)[1] + "_legend_circle_glower")
            .transition()
            .duration(transitionRate)
            .attr("r", function (d, i){
                var radius = d3.select(this).datum()["radius"];
                if (status > 0) {
                    return radius * 1.5;
                }
                else {return 0;}
            })
            .style("filter", "url(#glow)");
}

function transition(grantMovement, route, grantToDraw, newDraw, realTimeInfo, flightSpeed) {
    var l = route.node().getTotalLength();

    grantMovement.transition()
        .duration(l * flightSpeed)
        .attrTween("transform", delta(grantMovement, route.node()))
        .each("end", function() {
            //Delete the spent route.
            route.remove();

            //Update record of which grants are currently airborne
            if (fundingAgencyFlightStatus[grantToDraw["funderName"]] > 0){
                 fundingAgencyFlightStatus[grantToDraw["funderName"]] -= 1
            }

            //Scale the circles in the legend by circles current in flight
            legendCircleActivityScaler(grantToDraw)

            //Add points on the Earth when the grants lands
            setTimeout(terrestrialPoints(newDraw, grantToDraw, realTimeInfo, largestTotalGrantByOrg), 125);

        }).remove(); //remove the moving circle
}

function grantTranslate(grantToDraw, newDraw, realTimeInfo, flightSpeed) {
    //Model Params
    var k = 0.7;
    var c = 0.3;
    var minValue = 7;

    var from = funderGeoDict[grantToDraw["funderName"]];
    var to = funderGeoDict[grantToDraw["grantRecipientOrg"]];
    var movingGrantRadius = logistic_fn(grantToDraw["grantAmount"], minValue, largestSingleGrant, k, c);

    var route = funderLayer.append("path")
                   .attr("fill-opacity", 0)
                   .datum({type: "LineString", coordinates: [from, to]})
                   .attr("class", "route")
                   .attr("d", path);

    var grantMovement = g.append("svg:circle")
                            .attr("class", "grantMovement")
                            .attr("fill", funderColors[grantToDraw["funderName"]])
                            .attr("r", movingGrantRadius)
                            .attr("fill-opacity", 0.85);

    transition(grantMovement, route, grantToDraw, newDraw, realTimeInfo, flightSpeed);
}

function fillArray(value, len) {
    //See: http://stackoverflow.com/a/12503237/4898004.
    var arr = [];
    for (var i = 0; i < len; i++) {arr.push(value);}
    return arr;
}

function grantTranslateMaster(arrayOfGrantsToDraw, movementRate, flightSpeed){
    var newDraw = false;
    var priorFundingRecipients = [];
    var realTimeInfo = {};

    var i = 0;
    var complete = false;
    var animationIntervalID = setInterval(function(){
        if (i > arrayOfGrantsToDraw.length - 2) {complete = true;}

        newDraw = false;
        var grantToDraw = arrayOfGrantsToDraw[i];
        var grantAmount = grantToDraw["grantAmount"];
        var funderAbrev = funderNameAbbreviation[grantToDraw["funderName"]];

        if (priorFundingRecipients.indexOf(grantToDraw["recipientUniqueGeo"]) === -1){
            newDraw = true;
            var newOrg = fillArray(funderAbrev, grantToDraw["numberOfGrants"]);

            priorFundingRecipients.push(grantToDraw["recipientUniqueGeo"]);
            realTimeInfo[grantToDraw["recipientUniqueGeo"]] = [grantAmount, newOrg];
        } else {
            var previousAmount = realTimeInfo[grantToDraw["recipientUniqueGeo"]][0];
            var previousOrgs = realTimeInfo[grantToDraw["recipientUniqueGeo"]][1];
            var newOrg = fillArray(funderAbrev, grantToDraw["numberOfGrants"]);

            realTimeInfo[grantToDraw["recipientUniqueGeo"]] = [
                previousAmount + grantAmount,
                previousOrgs.concat(newOrg)
            ];
        }

        //Update Record of Airborn Grants
        if (!(grantToDraw["funderName"] in fundingAgencyFlightStatus)){
            fundingAgencyFlightStatus[grantToDraw["funderName"]] = 1
        } else {
            fundingAgencyFlightStatus[grantToDraw["funderName"]] += 1
        }

        grantTranslate(grantToDraw, newDraw, realTimeInfo, flightSpeed);

        //Update Date
        //This is here to insure a linear flow for the time stamp. Pretty rigorous procedure.
        //It is a bit of a fudge factor, but as the input funding csv will always be
        //in proper descending order prior to export from pandas in python, this *should* act to smooth
        //out erroneous date time updates which emerge from variability in d3 rendering.
        var newDateToDraw = grantToDraw["startDate"];
        if (dateRealTime.indexOf(newDateToDraw) === -1){
            dateRealTime.push(newDateToDraw)
            svg.selectAll("text").text(function(d) {
                var currentDate = d3.select(this).text()
                if (dateChecker(newDateToDraw, currentDate)){
                    return newDateToDraw;
                } else {
                    return currentDate;
                }
            });
        //Update the Current Year
        if (currentYear != newDateToDraw.slice(-4)) {currentYear = newDateToDraw.slice(-4)}
        }

        // Stop when complete...
        if (complete === true){
            //Remove all glow on exit.
            for (var key in fundingAgencyFlightStatus){
                d3.selectAll("#container2")
                    .select("#" + key.match(/\((.*?)\)/)[1] + "_legend_circle_glower")
                    .attr("r", 0)
            }
            clearInterval(animationIntervalID);
        }
        //Pump counter.
        i++;
    }
    , movementRate);
}

//----------------------------------------------------------------------------------------//

// Constructing the Initial Map

function legendTooltipInfo(name, taskType){
    var fullName = abbreviationFunderName[name];
    var title = fullName.replace(/\((.*?)\)/, "").trim();
    var yearlyFunderInfo = funderYearByYear[currentYear];

    if (yearlyFunderInfo.hasOwnProperty(fullName)){
        if (taskType === 1){return true;}
        var totalGrants = accounting.formatMoney(yearlyFunderInfo[fullName][0]) + " USD";
        var percent = yearlyFunderInfo[fullName][1] + "%";
    } else {
        if (taskType === 1){return false;}
        var totalGrants = "$0.00" + " USD";
        var percent = "0.00%"
    }
    var totalGrantsInfo = "<em>" + "Total Grants Starting in " + currentYear + ": " + "</em>" + totalGrants + "</br>" + " (~" + percent + " of total)";

    var fullTooltip = "<strong>" + title + "</strong>" + "</br>" + totalGrantsInfo + "</br>";
    return fullTooltip;
}

function legendGenerator(legend, currentWidth){
    var yCircleSpace = 80;
    var yTextSpace = yCircleSpace * 1.35;
    var legendCircleSize = 40;

    var legendToDraw = {}
    for (var key in funderColors){
        if (fundersPresentInDB.indexOf(key) != -1){
            legendToDraw[key] = funderColors[key]
        }
    }

    var spaceIncrement = currentWidth/fundersPresentInDB.length;
    var spacer = (currentWidth - currentWidth/spaceIncrement)/25;

    for (var key in legendToDraw) {
        var abbreiv = key.match(/\((.*?)\)/)[1];
        var fColor = legendToDraw[key];

        var legendCircleTypes = ["glower", "reg"];
        for (var t in legendCircleTypes) {
            legend.attr("class", "legend")
                .append("svg:circle")
                .attr("cx", spacer)
                .attr("cy", yCircleSpace)
                .attr("class", "legend")
                .style("fill", fColor)
                .attr("id", abbreiv + "_legend_circle_" + legendCircleTypes[t])
                .attr("r", legendCircleSize)
                .datum({"radius" : legendCircleSize, "name" : abbreiv.split("_")[0]})
                .on("mousemove", function (d) {
                    var name = d3.select(this).attr("id").split("_")[0];
                    var offsetL = -document.getElementById("container2").offsetLeft;
                    var offsetT = legendBoxHeight - legendBoxHeight/1.2;
                    showTooltip(d, tooltipContainer2, legendTooltipInfo(name, 0), offsetL, offsetT);
                    //Scale Corresponding Map point up
                    d3.selectAll(".funderpoints")
                        .select("#" + name)
                        .transition()
                        .duration(250)
                        .attr("r", function (d, i){
                            var s = zoom.scale();
                            return pointScale(d3.select(this).datum(), s) * 4.5;
                        });
                })
                .on("mouseout", function () {
                    var name = d3.select(this).attr("id").split("_")[0];
                    hideTooltip(tooltipContainer2);
                    //Scale Corresponding Map point down
                    d3.selectAll(".funderpoints")
                        .select("#" + name)
                        .transition()
                        .duration(250)
                        .attr("r", function (d, i){
                            var s = zoom.scale();
                            return pointScale(d3.select(this).datum(), s);
                        });
                });
        }

        legend.attr("class", "legend")
            .append("text")
            .attr("x", spacer)
            .attr("y", yCircleSpace + yTextSpace)
            .attr("id", abbreiv + "_legend_text")
            .attr("dy", ".35em")
            .attr("text-anchor", "middle")
            .style("font", "Lucida Grande")
            .style("font-size", "45px")
            .style("opacity", 1)
            .text(abbreiv);

        spacer += spaceIncrement;
    }
}

function valuesFromObject(inputObject){
    //See: http://stackoverflow.com/a/25797464/4898004.
    return Object.keys(inputObject).map(function(key){return inputObject[key]})
}

function individualGrantExtractor(d, amount, recipientUniqueGeo, orgFundingInfoTemp){

    //Add the lng and lat of an Org; to do: first check if it already exists.
    var orgLocation = [d["lng"], d["lat"]].map(parseFloat);

    //Add Movement of Fund
    var gmovement = {
            "funderName"         : d["FunderNameFull"],
            "grantRecipientOrg"  : d["OrganizationName"],
            "startDate"          : d["StartDate"],
            "uID"                : d["uID"],
            "numberOfGrants"     : parseInt(d["NumberOfGrants"]),
            "grantAmount"        : amount,
            "recipientUniqueGeo" : recipientUniqueGeo
    };
    return {"gmovement" : gmovement, "orgLocation" : orgLocation}
}

function objConcat(object1, object2) {
    for (var i in object2) {
        if (object2.hasOwnProperty(i)) {
            object1[i] = object2[i];
        }
    }
    return object1;
}

function drawMain(simulationSpeed, flightSpeed) {
    var startDate = "";

    var yearsInDb = [];
    var routesToDraw = [];
    var grantMovements = [];
    var orgFundingInfoTemp = {};

    d3.json("data/starter_kit/data/world-topo-min.json", function(error, world) {
        topo = topojson.feature(world, world.objects.countries).features;

        var country = g.selectAll(".country").data(topo);
        country.enter().insert("path")
                        .attr("class", "country")
                        .attr("d", path)
                        .style("fill", "#383838");

        var offsetL = document.getElementById("container").offsetLeft+0;
        var offsetT = document.getElementById("container").offsetTop+10;

        d3.csv("data/funder_db.csv", function(error, funder){
            funder.forEach(function (d) {
                var abbreviation = d["funder"].match(/\((.*?)\)/)[1];
                addFunderPoints(d["lng"], d["lat"], 12, d["funder"], d["colour"], 0.85);
                funderGeoDict[d["funder"]] = [d["lng"], d["lat"]].map(parseFloat);
                funderColors[d["funder"]] = d["colour"]
                funderColorsAbbreviation[abbreviation] = d["colour"]
                funderNameAbbreviation[d["funder"]] = abbreviation
                abbreviationFunderName[abbreviation] = d["funder"]
            });

            d3.csv("data/organization_rankings.csv", function(error, recipient) {
                recipient.forEach(function (d) {
                    recipientRankings[d["OrganizationName"]] = parseInt(d["OrganizationRank"])
                })
            });

            //Add Summary Information for each Agency for each Year
            d3.csv("data/funding_yearby_summary.csv", function(error, funder) {
                funder.forEach(function (d) {
                    //Set the starting year
                    if (currentYear === ""){currentYear = d["Year"]}

                    var funderInfoObj = {};
                    funderInfoObj[d["FunderNameFull"]] = [parseFloat(d["TotalGrants"]), d["PercentTotalGrants"]];

                    if (!(funderYearByYear.hasOwnProperty(d["Year"]))){
                        funderYearByYear[d["Year"]] = funderInfoObj;
                    } else {
                        funderYearByYear[d["Year"]] = objConcat(funderYearByYear[d["Year"]], funderInfoObj);
                    }
                })
            });

            //Add Funding Information
            d3.csv("data/funding_simulation_data.csv", function(error, grant){
                grant.forEach(function (d) {

                    //Get the Current Grant
                    var amount = parseFloat(d["NormalizedAmount"]);

                    if (!(isNaN(amount))) {

                        //Save the first date in the database
                        if (startDate === "") {startDate = d["StartDate"];}

                        var fromPoint = funderGeoDict[d["FunderNameFull"]].map(String);
                        var toPoint = [d["lng"], d["lat"]];

                        //If this is the largest grant, update.
                        if (amount > largestSingleGrant) {largestSingleGrant = amount;}

                        var recipientUniqueGeo = (d["lng"] + d["lat"]).replace(/ /g, "") + d["OrganizationName"];

                        //Update Grants by Orginization in the database.
                        if (orgFundingInfoTemp[recipientUniqueGeo] === undefined) {
                            orgFundingInfoTemp[recipientUniqueGeo] = amount
                        } else {
                            orgFundingInfoTemp[recipientUniqueGeo] += amount
                        }

                        if (fundersPresentInDB.indexOf(d["FunderNameFull"]) === -1){
                            fundersPresentInDB.push(d["FunderNameFull"])
                        }

                        var singleGrant = individualGrantExtractor(d, amount, recipientUniqueGeo, orgFundingInfoTemp);
                        grantMovements.push(singleGrant["gmovement"]);

                        funderGeoDict[d["OrganizationName"]] = singleGrant["orgLocation"];
                        routesToDraw.push(fromPoint);
                        routesToDraw.push(toPoint);
                    }
                });
                //Add Legend
                var currentWidth = document.getElementById("container2").offsetWidth;
                legend = gLwr.append("g").attr("class", "legend");
                legendGenerator(legend, currentWidth);

                //Add DateBox
                addDate(startDate);

                //Work out the largest grant for a single Org.
                largestTotalGrantByOrg = Math.max.apply(null, valuesFromObject(orgFundingInfoTemp));

                // ***Run the Simulation*** ///
                grantTranslateMaster(grantMovements, simulationSpeed, flightSpeed);

                //Clear orgFundingInfoTemp from memory
                orgFundingInfoTemp = {};
            });
        });
    });
}

//----------------------------------------------------------------------------------------//

// Tools for plotting funders

function funderCircleAppend(appendTo, x, y, color, opacity, r, info){
    appendTo.append("svg:circle")
        .attr("cx", x)
        .attr("cy", y)
        .attr("class","funderpoint")
        .style("fill", color)
        .style("opacity", opacity)
        .attr("id", info.match(/\((.*?)\)/)[1])
        .attr("r", r)
        .datum(r)
        .on("mousemove", function(d) {
            showTooltip(d
                        , tooltipContainer
                        , "<strong>" + info + "</strong>"
                        , document.getElementById("container").offsetLeft
                        , document.getElementById("container").offsetTop+10
        )})
        .on("mouseout",  function() {
            hideTooltip(tooltipContainer)
        });
}

//function to add points and text to the map (used in plotting grants)
function addFunderPoints(lat, lon, amount, name, color, opacity) {
    var funderpoints = funderLayer.append("g").attr("class", "funderpoints");
    var location = projection([lat, lon]);

    funderCircleAppend(funderpoints, location[0], location[1], color, opacity, amount, name);
}

//----------------------------------------------------------------------------------------//

//General Mechanics
var simulationSpeed = 0.01;
var flightSpeed = 7;

function redraw() {
    //to do:
    //Correct window resize (i.e., edit setup())
    width = document.getElementById("container").offsetWidth;
    height = width / 2;
    d3.select("#container").select("svg").remove();
    d3.select("#container2").select("svg").remove();
    setup(width, height);
    drawMain(simulationSpeed, flightSpeed);
}

function pointScale(amount, zoomScale){
    var size = amount * (5/zoomScale);

    if (size > amount) {
        return amount;
    } else {
        return size;
    }
}

function zoomer() {
    var t = d3.event.translate;
    var s = d3.event.scale;
    var h = height/4;

    t[0] = Math.min(
        (width/height) * (s - 1),
        Math.max(width * (1 - s), t[0])
    );

    t[1] = Math.min(
        h * (s - 1) + h * s,
        Math.max(height  * (1 - s) - h * s, t[1])
    );

    var transformCmd = "translate(" + t + ")scale(" + s + ")";
    g.attr("transform", transformCmd);
    funderLayer.attr("transform", transformCmd);

    // Change circle size based on zoom level.//
    d3.selectAll(".funderpoints")
        .selectAll("circle")
        .attr("r", function (d, i){
            var currentRadius = d3.select(this).datum();
            return pointScale(currentRadius, s);
    });
    d3.selectAll(".institution")
        .selectAll("circle")
        .attr("r", function (d, i){
            var currentRadius = d3.select(this).datum();
            return pointScale(currentRadius, s);
    });

    //Correct the routes for zooming and panning.//
    g.selectAll(".route")
        .attr("transform", transformCmd)
        .attr("d", path.projection(projection));
}

var throttleTimer;
function throttle() {
    window.clearTimeout(throttleTimer);
    throttleTimer = window.setTimeout(function() {
    redraw();
    }, 100);
}

//----------------------------------------------------------------------------------------//

//Execute Simulation -- smaller = faster.
drawMain(simulationSpeed, flightSpeed);

















































