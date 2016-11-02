/**
 * Funding Keyword Text Mining Visualization
 * Tariq A. Hassan, 2016.
*/

//----------------------------------------------------------------------------------------

//Initialize

var currentYear = -1;
var agencyRadius, finalAgencySpacer, circle, text;

var years = [];
var allSections = [];
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

//Foreground Layers
var keywords = svg.append("g");
var agencies = svg.append("g");
var yearTransition = svg.append("g");

//----------------------------------------------------------------------------------------

//Draw Text

function drawText(toAttach, x, y, text, textClass, opacity, textOptions){
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
    yearTransition.append("path")
        .attr("transform", function(d) { return "translate(" + x + "," + y + ")"; })
        .attr("d", d3.svg.symbol()
            .type("triangle-" + direction)
            .size(size * 1000)
        )
        .attr("class", "year")
        .style("fill", fill)
        .datum([size * 1000, direction])
        .on("click", function(d){
            var currentSize = d3.select(this).datum()[0];
            var newSize = currentSize * 1.35;

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
    var xPosition = 2750;
    var yPosition = 1300;
    var yUpper = yPosition - 100;
    var yLower = yPosition + 100;
    var yText = yUpper + Math.abs(yLower - yUpper) / 2; // abs() not really needed here...

    if (drawNew == true) {
        textOptions = {"anchor" : "middle", "fill" : "black", "size" : "70px", "weight" : "normal"}

        //Add the year
        drawText(yearTransition, xPosition, yText, String(year), "year", 1, textOptions)

        //Upper Triangle
        triangleDraw(xPosition, yUpper, 9.5, "green", 'up')

        //Lower Triangle
        triangleDraw(xPosition, yLower, 9.5, "red", 'down')
    } else {
        d3.select(".year").text(String(year))
    }
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
    var current;
    for (var i in lines) {
        current = lines[i].id

        if (current != "") {

            //Get the new line Opacities
            defaultOpacity = d3.select("#" + current).datum()['opacity'];
            newOpacities = determineAdjustments(adjustments, defaultOpacity);

            //Apply opacity change
            if (increaseOpacityTest(current, agencyAbbreviation) === true) {
                d3.select("#" + current).attr("opacity", newOpacities[0])
            } else {
                d3.select("#" + current).attr("opacity", newOpacities[1])
            }
        }
    }
}

function barSectionHighlight(agencyAbbreviation, mouseMovementType){
    var agencyColor;
    var hoverChange = 0;
    var notHoverChange = 0;

    if (mouseMovementType === "mouseover"){
        hoverChange = 0.08;
        notHoverChange = -0.12;
    }

    if (agencyAbbreviation in keywordSectionTracker){
        var keywordBarSections = keywordSectionTracker[agencyAbbreviation];

        for (var s in allSections){
            agencyColor = agencyColors[sectionAgencyTracker[allSections[s]][0]]

            if (keywordBarSections.indexOf(allSections[s]) != -1){
                d3.select("#" + allSections[s]).attr("fill", shadeColor2(agencyColor, hoverChange))
            } else {
                d3.select("#" + allSections[s]).attr("fill", shadeColor2(agencyColor, notHoverChange))
            }
        }
    } else {
        for (var s in allSections){
            agencyColor = agencyColors[sectionAgencyTracker[allSections[s]][0]]
            d3.select("#" + allSections[s]).attr("fill", shadeColor2(agencyColor, notHoverChange))
        }
    }
}

//----------------------------------------------------------------------------------------

//Draw circles for the agencies

function agencyDraw(agencyName, colour, agencyRadius, yLocation){
    var xLocation = 350;
    var agencyAbbreviation = agencyName.match(/\((.*?)\)/)[1]

    agencies.append("circle")
            .attr("class", "agency")
            .attr("cx", xLocation)
            .attr("cy", yLocation)
            .attr("r", agencyRadius)
            .attr("id", agencyAbbreviation)
            .datum([xLocation, yLocation, colour, agencyRadius])
            .style("fill", colour)
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
                         xLocation - agencyRadius * 4.5,
                         yLocation + agencyRadius/3.3,
                         agencyAbbreviation, "agency", 0, "default")

    var bbox = label[0][0].getBBox();

    drawText(agencies,
             xLocation/2.5 - bbox.width/2,
             yLocation + bbox.height/2.8,
             agencyAbbreviation, "agency", 1, "default")
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
    return object
}

// function objConcat(object1, object2) {
//     for (var i in object2) {
//         if (object2.hasOwnProperty(i)) {
//             object1[i] = object2[i];
//         }
//     }
//     return object1;
// }
//
// function nestedObjectAdd(obj, key, newKey, newValue){
//     var newObj = {};
//     newObj[newKey] = newValue
//
//     if (!(obj.hasOwnProperty(key))){
//         obj[key] = newObj;
//     } else {
//         var current = obj[key];
//         obj[key] = objConcat(obj[key], newObj)
//     }
//     return obj
// }

//----------------------------------------------------------------------------------------

//Keyword Helper Functions

function shadeColor2(color, percent) {
    //See: http://stackoverflow.com/questions/5560248/programmatically-lighten-or-darken-a-hex-color-or-rgb-and-blend-colors
    //Amazing Answer
    var f=parseInt(color.slice(1),16),t=percent<0?0:255,p=percent<0?percent*-1:percent,R=f>>16,G=f>>8&0x00FF,B=f&0x0000FF;
    return "#"+(0x1000000+(Math.round((t-R)*p)+R)*0x10000+(Math.round((t-G)*p)+G)*0x100+(Math.round((t-B)*p)+B)).toString(16).slice(1);
}

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
        breakIndex = middleKeyword
    } else {
        breakIndex = middleKeyword + 1
    }
    var upperHalf = keywords.slice(0, breakIndex).reverse()
    var lowerHalf = keywords.slice(breakIndex, keywords.length)
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
        indexOfLargestValue = getMaxNested(inputArray, indexOfInterest)

        reordered.push(inputArray[indexOfLargestValue])

        inputArray = indexRemove(inputArray, indexOfLargestValue)
    }
    return reordered
}

function millionBillionScaler(amount){
    var scaledAmount = amount/1000000000;

    if (scaledAmount.toFixed(1)[0] == "0"){
        scaledAmount = amount/1000000
        return [scaledAmount.toFixed(1), "M"]
    } else {
         return [scaledAmount.toFixed(1), "B"]
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

function keywordDraw(year, yPosition, keyword, height){
    var xPosition = 1800;
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
        currentXPosition = xPosition + currentXDisplacement[currentEntry[1]] - sectionWidth;
        sectionNumber = numberOfSections[currentEntry[1]];

        //Save which agency has which bar sections
        objectKeyArrayAdd(keywordAgencyMapping, keywordID, currentEntry[0])
        objectKeyArrayAdd(sectionAgencyTracker, keywordID + "_" + sectionNumber, currentEntry[0])
        objectKeyArrayAdd(keywordSectionTracker, currentEntry[0], keywordID + "_" + sectionNumber)

        //Save to array of current sections
        allSections.push(keywordID + "_" + sectionNumber)

        keywords.append("rect")
                .attr("class", "keywords")
                .datum([xPosition, yPosition, height])
                .attr("x", currentXPosition)
                .attr("y", yPosition)
                .attr("id", keywordID + "_" + sectionNumber)
                .attr("width", sectionWidth)
                .attr("height", height)
                .attr("fill", barColor)
                .attr("stroke", barColor)
                .on("mouseover", function(d){
                    lineHighlight(keywordAgencyPairsGen(keywordID), [0.35, -0.35])
                })
                .on("mouseout", function(d){
                    lineHighlight(keywordAgencyPairsGen(keywordID), "reset")
                });

    }
    //Label the bar
    drawText(keywords,
         currentXPosition + sectionWidth + 15,
         yPosition + (height / 2),
         keywordID + " ($" + currencyAmount[0] + currencyAmount[1] + ")",
         "keywords", 1, "default")
}

function keywordYearDraw(year){
    //Draws the keywords for a given year.
    //  The first half of the keywords are draw below the
    //  midpoint of the agency circles column; the second half are draw above.
    var adjustment, resetAdjustment;
    var keywords = keywordByYear[year];
    var agencyTrueLength = (finalAgencySpacer - agencyRadius * 1.5);
    var agencyMidpoint = agencyTrueLength/1.90;
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
    }
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

    background.append("line")
        .attr("class", "connection")
        .attr("id", agency + "_to_" + keyword)
        .attr("x1", p1[0])
        .attr("y1", p1[1])
        .attr("x2", p2[0] + p2[0] * 0.008)
        .attr("y2", p2[1] + p2[2]/2)
        .attr("stroke", p1[2])
        .attr("stroke-width", defaultLineWidth * widthScale)
        .attr("opacity", 0.50)
        .datum({'opacity': 0.50});
}

function keywordTransition(year, drawNew){

    //Update tracker
    yearClicker(year, drawNew)

    //Get the Data for the current Year
    var currentYearData = yearToYearMapping[year];

    //Remove the old keywords & lines
    d3.selectAll(".keywords").remove();
    d3.selectAll(".connection").remove();

    //Clean keywords from prior year
    allSections = [];
    sectionAgencyTracker = {};
    keywordSectionTracker = {};

    //Draw the keywords
    keywordYearDraw(year);

    for (var d in currentYearData){
        drawConnection(currentYearData[d][0], currentYearData[d][1])
    }
}


//----------------------------------------------------------------------------------------

//Main Drawing Function

function mainDraw(){
    //Agencies
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









































































