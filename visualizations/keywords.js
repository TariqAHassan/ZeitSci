/**
 * Funding Keyword Text Mining Visualization
 * Tariq A. Hassan, 2016.
*/

//----------------------------------------------------------------------------------------

//Initialize
var widestBar = [-1, -1];
var currentYear = -1;
var agencyRadius, finalAgencySpacer, circle, text, agencyXPosition, barXStartingPosition;

//Arrays
var years = [];
var allSections = [];
var minMaxKeywordYSpacers = []

//Objects
var agencyColors = {};
var keywordByYear = {};
var yearToYearMapping = {};
var keywordAgencyMapping = {};
var sectionAgencyTracker = {};
var keywordSectionTracker = {};

//----------------------------------------------------------------------------------------

var bodySelection = d3.select("body");

var svg = bodySelection.append("svg")
                         .attr("width", document.getElementById("container").offsetWidth)
                         .attr("height", 3500);

//background Layer
var background = svg.append("g");
var infobox = svg.append("g");

//Foreground Layers
var keywords = svg.append("g");
var agencies = svg.append("g");
var yearTransition = svg.append("g");
var yearTransitionDate = svg.append("g");

//----------------------------------------------------------------------------------------//

//Tooltip Functionality

var tooltipContainer = d3.select("#container")
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

//----------------------------------------------------------------------------------------

//Draw Text

function drawText(toAttach, x, y, text, ID, textClass, opacity, textOptions){
    var textProperties = {
        "anchor" : "left",
        "fill" : "gray",
        "font" : "Lucida Grande",
        "size" : "45px",
        "weight" : "bold",
    }

    if (!(textOptions == 'default')){
        for (var k in textOptions){
            textProperties[k] = textOptions[k];
        }
    }

    var label = toAttach.append("text")
                        .attr("class", textClass)
                        .attr("id", ID)
                        .attr("x", x)
                        .attr("y", y)
                        .text(text)
                        .attr("dy", ".35em")
                        .attr("text-anchor", textProperties['anchor'])
                        .style("font", textProperties['font'])
                        .style("font-size", textProperties['size'])
                        .style("font-weight", textProperties['weight'])
                        .style("opacity", opacity)
                        .style('fill', textProperties['fill']);
    return label
}

//----------------------------------------------------------------------------------------

//Date Cycling

function triangleDraw(x, y, size, fill, direction){
    var sizeScaleFactor = 1800;

    yearTransition.append("path")
        .attr("d", d3.svg.symbol()
            .type("triangle-" + direction)
            .size(size * sizeScaleFactor)
        )
        .attr("transform", function(d) {
            return "translate(" + x + "," + y + ")";
        })
        .attr("class", "year" + "_" + direction)
        .style("fill", fill)
        .datum([size * sizeScaleFactor, direction])
        .on("click", function(d){
            var currentSize = d3.select(this).datum()[0];
            var newSize = currentSize * 1.70;

            //Scale up
            d3.select(this)
                .transition()
                .duration(100)
                .attr("d", d3.svg.symbol()
                                    .type("triangle-" + direction)
                                    .size(newSize))
            //Scale down
            d3.select(this)
                .transition()
                .delay(200)
                .attr("d", d3.svg.symbol()
                                    .type("triangle-" + direction)
                                    .size(currentSize))

            //Change the current year on button press if permitted
            if (d3.select(this).datum()[1] == "up"){
                if (!(years.indexOf(currentYear + 1) === -1)){
                    currentYear += 1
                }
            } else if (d3.select(this).datum()[1] == "down"){
                if (!(years.indexOf(currentYear - 1) === -1)){
                    currentYear -= 1
                }
            }
            //Update the Year
            keywordTransition(currentYear, false)
        })
}

function yearClicker(year, drawNew){
    //Position of Clicker
    var textOptions;
    var xPosition = barXStartingPosition + widestBar[0]/2;
    var yPosition = (minMaxKeywordYSpacers[0] + minMaxKeywordYSpacers[1]) / 2;
    var yText = yPosition

    var yearText, bbox;
    if (drawNew == true) {
        textOptions = {"anchor" : "middle", "fill" : "gray", "size" : "90px", "weight" : "normal"}

        //Add the year
        yearText = drawText(yearTransitionDate, xPosition, yText, String(year), "current_year", "year", 1, textOptions)
        bbox = yearText[0][0].getBBox();

        //Upper Triangle
        triangleDraw(xPosition, yPosition - bbox.height*1.20, 9.5, "green", 'up')

        //Lower Triangle
        triangleDraw(xPosition, yPosition + bbox.height*1.20, 9.5, "red", 'down')
    } else {
        d3.select(".year").text(String(year))
    }
}

//----------------------------------------------------------------------------------------

//Shade Color

function shadeColor2(color, percent) {
    //See: http://stackoverflow.com/questions/5560248/programmatically-lighten-or-darken-a-hex-color-or-rgb-and-blend-colors
    //Amazing Answer
    var f=parseInt(color.slice(1),16),t=percent<0?0:255,p=percent<0?percent*-1:percent,R=f>>16,G=f>>8&0x00FF,B=f&0x0000FF;
    return "#"+(0x1000000+(Math.round((t-R)*p)+R)*0x10000+(Math.round((t-G)*p)+G)*0x100+(Math.round((t-B)*p)+B)).toString(16).slice(1);
}

//----------------------------------------------------------------------------------------

//Highlighting

function determineAdjustments(adjustments, defaultOpacity){
    var selected, notSelected;
    //Determine how to adjust line opacity
    if (adjustments.constructor === Array) {
        selected = defaultOpacity + adjustments[0];
        notSelected = defaultOpacity + adjustments[1];
    } else if (adjustments === "reset") {
        selected = defaultOpacity;
        notSelected = defaultOpacity;
    }
    return [selected, notSelected]
}

function lineInAllowedPairs(lineID, keywordAgencyPairs){
    var lineAllowed = false;
    var lineSplit = lineID.split("_");
    var lineAgency = lineSplit[0];
    var lineKeyword = lineSplit[2];

    var currentPair;
    for (var p in keywordAgencyPairs){
        currentPair = keywordAgencyPairs[p]
        if (lineAgency == currentPair[0] && lineKeyword == currentPair[1]) {
            lineAllowed = true;
        }
    }
    return lineAllowed
}

function increaseOpacityTest(current, testAginst){
    if (testAginst.constructor === Array){
        return lineInAllowedPairs(current, testAginst) === true
    } else {
        return current.split("_")[0] == testAginst
    }
}

function lineHighlight(agencyAbbreviation, adjustments){
    var newOpacities, defaultOpacity;
    var lines = d3.selectAll(".connection")[0]

    //Loop though all the lines
    var currentLine, currentAgency;
    for (var i in lines) {
        currentLine = lines[i].id
        currentAgency = lines[i].id.split("_")[0]

        if (currentLine != "") {
            //Get the new line Opacities
            defaultOpacity = d3.select("#" + currentLine).datum()['opacity'];
            newOpacities = determineAdjustments(adjustments, defaultOpacity);

            //Apply opacity change
            if (increaseOpacityTest(currentLine, agencyAbbreviation) === true) {
                d3.select("#" + currentLine).attr("opacity", newOpacities[0])
            } else {
                d3.select("#" + currentLine).attr("opacity", newOpacities[1])
            }
        }
    }
}

function barSectionHighlight(agencyAbbreviation, mouseMovementType){
    var agencyColor, hoverChange, notHoverChange;

    if (mouseMovementType === "mouseover"){
        hoverChange = 0.08;
        notHoverChange = -0.125;
    } else {
        hoverChange = 0;
        notHoverChange = 0;
    }

    var changeToUse;
    if (agencyAbbreviation in keywordSectionTracker){
        var keywordBarSections = keywordSectionTracker[agencyAbbreviation];

        for (var s in allSections){
            agencyColor = agencyColors[sectionAgencyTracker[allSections[s]][0]]

            if (keywordBarSections.indexOf(allSections[s]) != -1){
                changeToUse = hoverChange;
            } else {
                changeToUse = notHoverChange;
            }
            d3.select("#" + allSections[s])
                .transition()
                .duration(125)
                .attr("fill", shadeColor2(agencyColor, changeToUse))
        }
    } else {
        for (var s in allSections){
            agencyColor = agencyColors[sectionAgencyTracker[allSections[s]][0]]
            d3.select("#" + allSections[s])
                .transition()
                .duration(125)
                .attr("fill", shadeColor2(agencyColor, notHoverChange))
        }
    }
}

//----------------------------------------------------------------------------------------

//Draw circles for the agencies

function agencyDraw(agencyName, colour, agencyRadius, yLocation){
    var agencyAbbreviation = agencyName.match(/\((.*?)\)/)[1]
    var fullName = agencyName.replace(agencyAbbreviation, "").replace("(","").replace(")","").trim()

    agencies.append("circle")
            .attr("class", "agency")
            .attr("cx", agencyXPosition)
            .attr("cy", yLocation)
            .attr("r", agencyRadius)
            .attr("id", agencyAbbreviation)
            .attr("fill", colour)
            .datum([agencyXPosition, yLocation, colour, agencyRadius])
            .on("mouseover", function(d){
                barSectionHighlight(agencyAbbreviation, "mouseover")
                lineHighlight(agencyAbbreviation, [0.35, -0.35])
            })
            .on("mouseout", function(d){
                barSectionHighlight(agencyAbbreviation, "mouseout")
                lineHighlight(agencyAbbreviation, "reset")
            })

    //Delete from the DOM after drawing...
    var label = drawText(agencies,
                         agencyXPosition - agencyRadius * 4.5,
                         yLocation + agencyRadius/3.3,
                         agencyAbbreviation, agencyAbbreviation,
                         "agency", 0, "default")

    var bbox = label[0][0].getBBox();

    keywords.append("text")
        .attr("class", "agency")
        .attr("x", agencyXPosition/2.5 - bbox.width/2)
        .attr("y", yLocation + bbox.height/25)
        .text(agencyAbbreviation)
        .attr("dy", ".35em")
        .attr("text-anchor", "left")
        .style("font", "Lucida Grande")
        .style("font-size", "45px")
        .style("font-weight", "bold")
        .style("opacity", 1)
        .style('fill', "gray")
        .on("mouseover", function(d){
            showTooltip(d, tooltipContainer
                        , "<strong>" + fullName + "</strong>"
                        , -65, -85)
        })
        .on("mouseout", function(d){
            hideTooltip(tooltipContainer)
        });
}

//----------------------------------------------------------------------------------------

//Object Manipulation

function objectKeyAdd(obj, key, newValue){
    if (!(obj.hasOwnProperty(key))){
        obj[key] = newValue
    } else {
        obj[key] += newValue
    }
    return obj
}

function objectKeyArrayAdd(obj, key, newValue){
    var updatedArray;
    if (!(obj.hasOwnProperty(key))){
        obj[key] = [newValue]
    } else {
        updatedArray = obj[key]
        updatedArray.push(newValue)
        obj[key] = updatedArray
    }
    return obj
}

function objectNestedListAdd(object, key, toAdd){
    if (!(object.hasOwnProperty(key))){
        object[key] = [toAdd];
    } else {
        var toAppend = object[key];
        toAppend.push(toAdd);
        object[key] = toAppend;
    }
    return object;
}

//----------------------------------------------------------------------------------------

//Keyword Helper Functions

function stringContains(inputString, agency, keyword){
    if (inputString.indexOf(agency) != -1 && inputString.indexOf(keyword) != -1){
        return true;
    } else {
        return false;
    }
}

function keywordOrder(keywords, middleKeyword){
    var breakIndex;
    if (keywords.length % 2 === 0) {
        breakIndex = middleKeyword;
    } else {
        breakIndex = middleKeyword + 1;
    }
    var upperHalf = keywords.slice(0, breakIndex).reverse();
    var lowerHalf = keywords.slice(breakIndex, keywords.length);
    return lowerHalf.concat(upperHalf);
}

function getMaxNested(inputArray, indexOfInterest){
    var max_index = -1;
    var largest_value = -1;
    for (var i in inputArray){
        if (inputArray[i][indexOfInterest] > largest_value){
            largest_value = inputArray[i][indexOfInterest]
            max_index = i
        }
    }
    return parseInt(max_index)
}

function indexRemove(inputArray, indexToRemove){
    //Not clear what is wrong with the splice() method
    //...but it's acting wierd here.
    var newArray = [];
    for (var i in inputArray){
        if (i != indexToRemove){
            newArray.push(inputArray[i])
        }
    }
    return newArray
}

function reorderNestedForMax(inputArray, indexOfInterest){
    var reordered = [];
    var indexOfLargestValue;

    for (var i in inputArray){
        indexOfLargestValue = getMaxNested(inputArray, indexOfInterest);

        reordered.push(inputArray[indexOfLargestValue]);

        inputArray = indexRemove(inputArray, indexOfLargestValue);
    }
    return reordered;
}

function millionBillionScaler(amount){
    var scaledAmount = amount/1000000000;

    if (scaledAmount.toFixed(1)[0] == "0"){
        scaledAmount = amount/1000000
        return [scaledAmount.toFixed(1), "M"];
    } else {
         return [scaledAmount.toFixed(1), "B"];
    }
}

//----------------------------------------------------------------------------------------

//Drawing the keywords

function keywordAgencyPairsGen(keywordID){
    var agenciesInCurrentBar = keywordAgencyMapping[keywordID];

    var keywordAgencyPairs = [];
    for (var k in agenciesInCurrentBar){
        keywordAgencyPairs.push([agenciesInCurrentBar[k], keywordID])
    }
    return keywordAgencyPairs
}

function matchingKeywordsExtractor(currentYearData, keywordID){
    //Extract
    var entriesMatchingKeywordID = [];
    for (var s in currentYearData){
        var currentEntry = currentYearData[s]
        if (currentEntry[1] == keywordID){
            entriesMatchingKeywordID.push(currentEntry);
        }
    }
    //Reorder
    return reorderNestedForMax(entriesMatchingKeywordID, 3)
}

function agencyCircleColorAdj(pairs, mouseMovementType){
    var agency = [];
    var hoverChange, notHoverChange;

    if (mouseMovementType === "mouseover"){
        hoverChange = 0.08;
        notHoverChange = -0.125;
    } else {
        hoverChange = 0;
        notHoverChange = 0;
    }

    //Get the agencies which fund the selected keyword
    for (var i in pairs){
        if (agency.indexOf(pairs[i][0]) === -1) {
            agency.push(pairs[i][0]);
        }
    }

    // Apply the color changes
    var changeToUse;
    for (var a in agencyColors){
        if (agency.indexOf(a) != -1){
            changeToUse = hoverChange;
        } else {
            changeToUse = notHoverChange;
        }
        d3.select("#" + a)
            .transition()
            .duration(150)
            .attr("fill", shadeColor2(agencyColors[a], changeToUse))
    }
}

function keywordDraw(year, yPosition, keyword, height){
    barXStartingPosition = barXPositionCalculator();
    var keywordID = keyword[0];
    var totalWidth = keyword[2];
    var currencyAmount = millionBillionScaler(keyword[1]);

    var barColor, sectionWidth, sectionNumber, currentXPosition;
    var numberOfSections = {};
    var currentXDisplacement = {};

    var currentYearData = yearToYearMapping[year];
    var orderedMatchingEntries = matchingKeywordsExtractor(currentYearData, keywordID);

    //Draw each bar
    for (var s in orderedMatchingEntries){
        var currentEntry = orderedMatchingEntries[s]

        numberOfSections = objectKeyAdd(numberOfSections, currentEntry[1], 1);
        sectionWidth = totalWidth * currentEntry[3];
        currentXDisplacement = objectKeyAdd(currentXDisplacement, currentEntry[1], sectionWidth);

        barColor = d3.select("#" + currentEntry[0]).datum()[2]
        currentXPosition = barXStartingPosition + currentXDisplacement[currentEntry[1]] - sectionWidth;
        sectionNumber = numberOfSections[currentEntry[1]];

        //Save which agency has which bar sections
        objectKeyArrayAdd(keywordAgencyMapping, keywordID, currentEntry[0])
        objectKeyArrayAdd(sectionAgencyTracker, keywordID + "_" + sectionNumber, currentEntry[0])
        objectKeyArrayAdd(keywordSectionTracker, currentEntry[0], keywordID + "_" + sectionNumber)

        //Save to array of current sections
        allSections.push(keywordID + "_" + sectionNumber)

        keywords.append("rect")
                .attr("class", "keywords")
                .datum([barXStartingPosition, yPosition, sectionWidth, height])
                .attr("x", currentXPosition)
                .attr("y", yPosition)
                .attr("id", keywordID + "_" + sectionNumber)
                .attr("width", sectionWidth)
                .attr("height", height)
                .attr("fill", barColor)
                .attr("stroke", barColor)
                .on("mouseover", function(d){
                    var pairs = keywordAgencyPairsGen(keywordID)
                    lineHighlight(pairs, [0.35, -0.35])
                    agencyCircleColorAdj(pairs, "mouseover")
                })
                .on("mouseout", function(d){
                    var pairs = keywordAgencyPairsGen(keywordID)
                    lineHighlight(pairs, "reset")
                    agencyCircleColorAdj(pairs, "mouseout")
                });

    }
    //Label the bar
    drawText(keywords,
         currentXPosition + sectionWidth + 15,
         yPosition + (height / 2),
         keywordID + " ($" + currencyAmount[0] + currencyAmount[1] + ")",
         keywordID, "keywords", 1, "default")
}

function keywordYearDraw(year){
    //Draws the keywords for a given year.
    //  The first half of the keywords are draw below the
    //  midpoint of the agency circles column; the second half are draw above.
    var adjustment, resetAdjustment;
    var keywords = keywordByYear[year];
    var agencyTrueLength = (finalAgencySpacer - agencyRadius * 1.5);
    var agencyMidpoint = agencyTrueLength/1.825;
    var middleKeyword = parseInt(keywords.length/2);
    var keywordSpaceFactor = 1.3;

    //Add half of the rect height to the midpoint

    //Use the Length of Agency Column, in combination with the keywordSpaceFactor
    //to work our the max. size a keyword rectange can be.
    var keywordHeight = agencyTrueLength/(keywordSpaceFactor * keywords.length + 2.5);
    var keywordStep = keywordHeight * keywordSpaceFactor;

    //Use an Ugly counter variable
    //to track which keyword has been drawn
    var keywordCounter = 0;

    if (keywords.length % 2 === 0){
        adjustment = -1 * keywordHeight/2;
        resetAdjustment = 0;
    } else {
        adjustment = 0;
        resetAdjustment = -1 * keywordHeight/2;
    }

    //Reordeer the keyword list for drawing
    //(midpoint --> first; first --> last)
    var keywordsOrdered = keywordOrder(keywords, middleKeyword);

    var arrayOfYKeywordSpacers = [agencyMidpoint + adjustment];

    var ySpacer = agencyMidpoint + adjustment;
    for (var k in keywordsOrdered){
        //Reset to the midpoint
        if (keywordCounter == middleKeyword){
            ySpacer = agencyMidpoint - keywordHeight - keywordStep/1.5 - resetAdjustment;
        }
        //Draw a keyword
        keywordDraw(year, ySpacer, keywordsOrdered[k], keywordHeight);

        if (keywordCounter < middleKeyword){
            ySpacer += keywordStep;
        } else {
            ySpacer -= keywordStep;
        }
        keywordCounter += 1;
        arrayOfYKeywordSpacers.push(ySpacer)
    }
    minMaxKeywordYSpacers = [Math.min.apply(null, arrayOfYKeywordSpacers), Math.max.apply(null, arrayOfYKeywordSpacers)];
}

function drawConnection(agency, keyword){
    //The Agency Location
    var p1 = d3.select("#" + agency).datum();

    //The Keyword Location
    var p2 = d3.select("#" + keyword + "_1").datum();

    //Default Line Width
    var defaultLineWidth = 85;

    var widthScale;
    var yearToYearData = yearToYearMapping[currentYear]
    for (var i in yearToYearData){
        if (yearToYearData[i][0] == agency && yearToYearData[i][1] == keyword){
            widthScale = yearToYearData[i][4]
        }
    }

    //Draw the line connecting an agency to a keyword
    background.append("line")
        .attr("class", "connection")
        .attr("id", agency + "_to_" + keyword)
        .attr("x1", p1[0])
        .attr("y1", p1[1])
        .attr("x2", p2[0] + p2[0] * 0.008)
        .attr("y2", p2[1] + p2[3]/2)
        .attr("stroke", p1[2])
        .attr("stroke-width", defaultLineWidth * widthScale)
        .attr("opacity", 0.50)
        .datum({'opacity': 0.50});
}

function keywordTransition(year, drawNew){

    //Get the Data for the current Year
    var currentYearData = yearToYearMapping[year];

    //Remove the old keywords & lines
    d3.selectAll(".keywords").remove();
    d3.selectAll(".connection").remove();

    //Clean keyword data from the prior year
    allSections = [];
    keywordAgencyMapping = {}
    sectionAgencyTracker = {};
    keywordSectionTracker = {};

    //Draw the keywords
    keywordYearDraw(year);

    //Update tracker
    yearClicker(year, drawNew)

    for (var d in currentYearData){
        drawConnection(currentYearData[d][0], currentYearData[d][1])
    }
}

//----------------------------------------------------------------------------------------

//Main Drawing Function

function barXPositionCalculator(){
    // total width - max length + leftSpace + agencyRadius
    var totalWidth = document.getElementById("container").offsetWidth;
    var minxBarPosition = agencyXPosition + agencyRadius + 20;
    var maxXBarPosition = totalWidth * 0.45;

    var start = totalWidth - widestBar[0] - 300;

    if (start > maxXBarPosition) {
        return parseInt(maxXBarPosition);
    } else if (start < minxBarPosition) {
        return parseInt(minxBarPosition);
    } else {
        return parseInt(start);
    }
}

function mainDraw(){
    //Agencies
    agencyXPosition = 350
    agencyRadius = 65;
    var yAgencySpacer = agencyRadius * 2.25;
    d3.csv("data/funder_db.csv", function(error, funder){
        funder.forEach(function (d) {
            //Save the color for each agency
            agencyColors[d["funder"].match(/\((.*?)\)/)[1]] = d["colour"]

            //Draw the agency circles
            agencyDraw(d["funder"], d["colour"], agencyRadius, yAgencySpacer);
            yAgencySpacer += agencyRadius * 2.25 + (agencyRadius * 0.75)
        });

        //Save the final step size
        finalAgencySpacer = yAgencySpacer;

        //Keywords Aggregated by Year
        d3.csv("keyword_data/funders_keywords_by_year.csv", function(error, keyword){
            keyword.forEach(function (d) {

            //Initialize the current year to the starting year
            if (currentYear === -1){
                currentYear = parseInt(d["Year"])
            }

            //Update the widest bar to be drawn
            if (d["ScaledAmount"] > widestBar[0]){
                widestBar = [parseFloat(d["ScaledAmount"]), d["Keywords"]]
            }

            var keywordData = [d["Keywords"],
                               parseFloat(d["NormalizedAmount"]),
                               parseFloat(d["ScaledAmount"])
            ];

            keywordByYear = objectNestedListAdd(keywordByYear, d["Year"], keywordData);

            //Add the year
            if (years.indexOf(parseInt(d["Year"])) === -1){
                years.push(parseInt(d["Year"]))
            }
            });

            //Read in data to connect the keywords to the funders
            d3.csv("keyword_data/funders_keywords.csv", function(error, funderKeywords){
                funderKeywords.forEach(function (d){
                    var connectionData = [d['Funder'],
                                          d['Keywords'],
                                          parseFloat(d['NormalizedAmount']),
                                          parseFloat(d['ProportionTotal']),
                                          parseFloat(d['ProportionYearlyTop'])
                    ]
                    //Update the mapping year to year for the keywords
                    yearToYearMapping = objectNestedListAdd(yearToYearMapping, d['Year'], connectionData)
                });
                //Draw the keywords for the first Year
                keywordTransition(currentYear, true)
            })
        })
    });
}

//----------------------------------------------------------------------------------------

//Generate the Figure

mainDraw();









































































