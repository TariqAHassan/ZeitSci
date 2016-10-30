/**
 * Funding Keyword Text Mining Visualization
 * Tariq A. Hassan, 2016.
*/


//Init
var circle;
var years = [];
var movementRate = 0.10;
var keywordByYear = {};
var yearToYearMapping = {};

//----------------------------------------------------------------------------------------

var bodySelection = d3.select("body");

var svg = bodySelection.append("svg")
                         .attr("width", document.getElementById("container").offsetWidth)
                         .attr("height", 3500);

//background Layer
var background = svg.append("g");

//Foreground Layer
var keywords = svg.append("g");

var agencies = svg.append("g");

function keywordTransition(yearToYearMapping, agencyLength, yStart, agencyRadius){
    movementRate = 3500;

    var i = 0;
    var complete = false;
    var animationIntervalID = setInterval(function(){
        if (i > years.length - 2){
            complete = true;
        }

        //Get the Data for the current Year
        var currentYearData = yearToYearMapping[years[i]];

        //Change the keywords//

        //Remove the old keywords
        d3.selectAll(".keywords").remove();
        d3.selectAll(".connection").remove();
        keywordYearDraw(years[i], keywordByYear, agencyLength, yStart, agencyRadius);

        for (var d in currentYearData){
            drawConnection(currentYearData[d][0], currentYearData[d][1])
        }

        if (complete === true){clearInterval(animationIntervalID);}
        i++;
        }
        , movementRate);
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
    var radius = 65;
    var yStart = radius * 2;
    var yAgencySpacer = yStart;
    d3.csv("data/funder_db.csv", function(error, funder){
        funder.forEach(function (d) {
            agencyDraw(d["funder"], d["colour"], radius, yAgencySpacer);
            yAgencySpacer += radius * 2 + (radius * 0.75)
    });
        //Keywords Aggregated by Year
        d3.csv("keyword_data/funders_keywords_by_year.csv", function(error, keyword){
            keyword.forEach(function (d) {

            var keyword = [d["Keywords"], parseFloat(d["NormalizedAmount"])];

            keywordByYear = objectNestedListAdd(keywordByYear, d["Year"], keyword);

            //Add the year
            if (years.indexOf(parseInt(d["Year"])) === -1){
                years.push(parseInt(d["Year"]))
            }
        });
            //Read in data to connect the keywords to the funders
            d3.csv("keyword_data/funders_keywords.csv", function(error, funderKeywords){
                funderKeywords.forEach(function (d){
                    var connectionData = [d['Funder'], d['Keywords'], parseFloat(d['NormalizedAmount'])]
                    //Update the mapping year to year for the keywords
                    yearToYearMapping = objectNestedListAdd(yearToYearMapping, d['Year'], connectionData)
                });
                keywordTransition(yearToYearMapping, yAgencySpacer, yStart, radius)
            })
        })
    });
}

function agencyDraw(name, colour, radius, yLocation){
    var xLocation = 125;
    var circleSelection = agencies.append("circle")
                             .attr("class", "agency")
                             .attr("cx", xLocation)
                             .attr("cy", yLocation)
                             .attr("r", radius)
                             .attr("id", name.match(/\((.*?)\)/)[1])
                             .datum([xLocation, yLocation, colour])
                             .style("fill", colour);
}

function keywordDraw(yPosition, id, height){
    var width = 450;
    var xPosition = 2000;

    var keywordRect = keywords.append("rect")
            .attr("class", "keywords")
            .attr("x", xPosition)
            .attr("y", yPosition)
            .attr("id", id[0])
            .attr("width", 450)
            .attr("height", height)
            .attr("fill", "navy")
            .attr("stroke", "black")
            .datum([xPosition, yPosition, height]);

    keywords.append("text")
            .attr("x", xPosition + (width / 3))
            .attr("y", yPosition + (height / 1.5))
            .text(id[0])
            .style("font", "Lucida Grande")
            .style("font-size", "45px")
            .style('fill', 'white');
}

function keywordYearDraw(year, keywordByYear, agencyLength, yStart, agencyRadius){
    //The first half of the keywords are draw below the
    //midpoint of the agency circles column; the second half are draw above.
    var keywords = keywordByYear[year];
    var agencyTrueLength = (agencyLength - agencyRadius*1.5);
    var agencyMidpoint = agencyTrueLength/2;
    var middleKeyword = parseInt(keywords.length/2);

    var keywordSpaceFactor = 1.1;

    //Use the Length of Agency Column, in combination with the keywordSpaceFactor
    //to work our the max. size a keyword rectange can be.
    var keywordHeight = agencyTrueLength/(keywordSpaceFactor * keywords.length);
    var keywordStep = keywordHeight * keywordSpaceFactor;

    //Use an Ugly counter variable
    //to track which keyword has been drawn
    var keywordCounter = 0;

    var ySpacer = agencyMidpoint;
    for (var k in keywords){

        //Reset to the midpoint
        if (keywordCounter == middleKeyword){
            ySpacer = agencyMidpoint
        }
        //Draw a keyword
        keywordDraw(ySpacer, keywords[k], keywordHeight);

        if (keywordCounter < middleKeyword){ySpacer += keywordStep}
        else {ySpacer -= keywordStep}
        keywordCounter += 1
    }
}

function drawConnection(agency, keyword){
    //The Agency Location
    var p1 = d3.select("#" + agency).datum();

    //The Keyword Location
    var p2 = d3.select("#" + keyword).datum();

    background.append("line")
        .attr("class", "connection")
        .attr("x1", p1[0])
        .attr("y1", p1[1])
        .attr("x2", p2[0] + p2[0] * 0.01)
        .attr("y2", p2[1] + p2[2]/2)
        .attr("stroke", p1[2])
        .attr("stroke-width", 25)
        .attr("opacity", 0.50);
}



mainDraw();




















