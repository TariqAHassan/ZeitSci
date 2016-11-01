/**
 * Funding Keyword Text Mining Visualization
 * Tariq A. Hassan, 2016.
*/


//Init
var agencyRadius, finalAgencySpacer, circle, text;

var currentYear = -1;

var years = [];
var keywordByYear = {};
var yearToYearMapping = {};

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

//Date Cycling

function triangleDraw(x, y, size, fill, direction){
    yearTransition.append("path")
        .attr("transform", function(d) { return "translate(" + x + "," + y + ")"; })
        .attr("d", d3.svg.symbol()
            .type("triangle-" + direction)
            .size(size * 1000)
        )
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

function yearText(year, x, y){
    text = yearTransition.append("text")
            .attr("class", "year")
            .attr("x", x)
            .attr("y", y)
            .attr("dy", ".35em")
            .attr("text-anchor", "middle")
            .style("font", "Lucida Grande")
            .style("font-size", "70px")
            .style("opacity", 1)
            .text(year);
}

function yearCycle(year, drawNew){

    //Position of Switcher
    var xPosition = 2500;
    var yPosition = 1300;
    var yUpper = yPosition - 100;
    var yLower = yPosition + 100;
    var yText = yUpper + Math.abs(yLower - yUpper) / 2; // abs() not really needed here...

    if (drawNew == true) {

        //Add the year
        yearText(String(year), xPosition, yText)

        //Upper Triangle
        triangleDraw(xPosition, yUpper, 9.5, "green", 'up')

        //Lower Triangle
        triangleDraw(xPosition, yLower, 9.5, "red", 'down')
    } else {
        d3.select(".year").text(String(year))
    }
}

//----------------------------------------------------------------------------------------

//Agency, Connection and Keyword Drawing

function keywordTransition(year, drawNew){

    //Update tracker
    yearCycle(year, drawNew)

    //Get the Data for the current Year
    var currentYearData = yearToYearMapping[year];

    //Remove the old keywords
    d3.selectAll(".keywords").remove();
    d3.selectAll(".connection").remove();

    //Draw the keywords
    keywordYearDraw(year);

    for (var d in currentYearData){
        drawConnection(currentYearData[d][0], currentYearData[d][1])
    }
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

function mainDraw(){
    //Agencies
    agencyRadius = 65;
    var yAgencySpacer = agencyRadius * 2;
    d3.csv("data/funder_db.csv", function(error, funder){
        funder.forEach(function (d) {
            //Draw the agency circles
            agencyDraw(d["funder"], d["colour"], agencyRadius, yAgencySpacer);
            yAgencySpacer += agencyRadius * 2 + (agencyRadius * 0.75)
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
                                          parseFloat(d['ProportionTotal'])
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

function lineHighlight(abbreviation, adjustments){
    var selected, notSelected;
    var lines = d3.selectAll(".connection")[0]

    //Loop though all the lines
    for (var i in lines) {
        var current = lines[i].id
        if (current != "") {
            var defaultOpacity = d3.select("#" + current).datum()['opacity'];

            //Determine how to adjust line opacity
            if (adjustments.constructor === Array){
                selected = defaultOpacity + adjustments[0];
                notSelected = defaultOpacity + adjustments[1];
            } else if (adjustments === "reset"){
                selected = defaultOpacity;
                notSelected = defaultOpacity;
            }

            //Apply opacity change
            if (current.split("_")[0] == abbreviation) {
                d3.select("#" + current).attr("opacity", selected)
            } else {
                d3.select("#" + current).attr("opacity", notSelected)
            }
        }
    }
}

function agencyDraw(agencyName, colour, agencyRadius, yLocation){
    var abbreviation = agencyName.match(/\((.*?)\)/)[1]
    var xLocation = 125;
    var circleSelection = agencies.append("circle")
                             .attr("class", "agency")
                             .attr("cx", xLocation)
                             .attr("cy", yLocation)
                             .attr("r", agencyRadius)
                             .attr("id", abbreviation)
                             .datum([xLocation, yLocation, colour, agencyRadius])
                             .style("fill", colour)
                             .on("mouseover", function(d){
                                 lineHighlight(abbreviation, [0.35, -0.35])
                             })
                            .on("mouseout", function(d){
                                lineHighlight(abbreviation, "reset")
                            })

}

//----------------------------------------------------------------------------------------

//Keyword Drawing Helper Functions

function keywordOrder(keywords, middleKeyword){
    var upper_half = keywords.slice(0, middleKeyword).reverse()
    var lower_half = keywords.slice(middleKeyword, keywords.length)
    return lower_half.concat(upper_half);
}

function objectKeyAdd(obj, key, newValue){
    if (!(obj.hasOwnProperty(key))){
        obj[key] = newValue
    } else {
        obj[key] += newValue
    }
    return obj
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

//----------------------------------------------------------------------------------------

//Drawing the keywords

function keywordDraw(year, yPosition, keyword, height){

    var xPosition = 1600;
    var keywordID = keyword[0];
    var totalWidth = keyword[2];

    var barColor;
    var currentXPosition;
    var sectionWidth;
    var numberOfSections = {};
    var currentXDisplacement = {};

    var currentYearData = yearToYearMapping[year];

    //Extract only the entries that match the keyword
    var entriesMatchingKeywordID = [];
    for (var s in currentYearData){
        var currentEntry = currentYearData[s]
        if (currentEntry[1] == keywordID){
            entriesMatchingKeywordID.push(currentEntry)
        }
    }

    //Order from largest to smallest
    var orderedMatchingEntries = reorderNestedForMax(entriesMatchingKeywordID, 3)

    //Draw each bar
    for (var s in orderedMatchingEntries){
        var currentEntry = orderedMatchingEntries[s]

        numberOfSections = objectKeyAdd(numberOfSections, currentEntry[1], 1)
        sectionWidth = totalWidth * currentEntry[3]
        currentXDisplacement = objectKeyAdd(currentXDisplacement, currentEntry[1], sectionWidth)

        barColor = d3.select("#" + currentEntry[0]).datum()[2]
        currentXPosition = xPosition + currentXDisplacement[currentEntry[1]] - sectionWidth

        keywords.append("rect")
                .attr("class", "keywords")
                .datum([xPosition, yPosition, height])
                .attr("x", currentXPosition)
                .attr("y", yPosition)
                .attr("id", keywordID + "_" + numberOfSections[currentEntry[1]])
                .attr("width", sectionWidth)
                .attr("height", height)
                .attr("fill", barColor)
                .attr("stroke", barColor);
    }
    //Label the bar
    keywords.append("text")
        .attr("class", "keywords")
        .attr("x", currentXPosition + sectionWidth + 15)
        .attr("y", yPosition + (height / 1.5))
        .text(keywordID)
        .style("font", "Lucida Grande")
        .style("font-size", "45px")
        .style("font-weight", "bold")
        .style('fill', 'gray');
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
    var keywordsOrdered = keywordOrder(keywords, middleKeyword)

    var ySpacer = agencyMidpoint + adjustment;
    for (var k in keywordsOrdered){

        //Reset to the midpoint
        if (keywordCounter == middleKeyword){
            ySpacer = agencyMidpoint - keywordHeight - keywordStep/1.5 - resetAdjustment;
        }

        //Draw a keyword
        keywordDraw(year, ySpacer, keywordsOrdered[k], keywordHeight);

        if (keywordCounter < middleKeyword){
            ySpacer += keywordStep
        } else {
            ySpacer -= keywordStep
        }
        keywordCounter += 1;
    }
}

function drawConnection(agency, keyword){
    //The Agency Location
    var p1 = d3.select("#" + agency).datum();

    //The Keyword Location
    var p2 = d3.select("#" + keyword + "_1").datum();

    background.append("line")
        .attr("class", "connection")
        .attr("id", agency + "_to_" + keyword)
        .attr("x1", p1[0])
        .attr("y1", p1[1])
        .attr("x2", p2[0] + p2[0] * 0.01)
        .attr("y2", p2[1] + p2[2]/2)
        .attr("stroke", p1[2])
        .attr("stroke-width", 25)
        .attr("opacity", 0.50)
        .datum({'opacity': 0.50});
}



mainDraw();

































