$(function(){

    // some defaults
    //Chart.defaults.global.responsive = true;

    var chartContainer = $("#chartContainer");

    Chart.Scale = Chart.Scale.extend({
      calculateX: function(index) {
        //check to ensure data is in chart otherwise we will get infinity
        if (!(this.valuesCount)) {
          return 0;
        }
        var isRotated = (this.xLabelRotation > 0),
          // innerWidth = (this.offsetGridLines) ? this.width - offsetLeft - this.padding : this.width - (offsetLeft + halfLabelWidth * 2) - this.padding,
          innerWidth = this.width - (this.xScalePaddingLeft + this.xScalePaddingRight),
          //if we only have one data point take nothing off the count otherwise we get infinity
          valueWidth = innerWidth / (this.valuesCount - ((this.offsetGridLines) || this.valuesCount === 1 ? 0 : 1)),
          valueOffset = (valueWidth * index) + this.xScalePaddingLeft;

        if (this.offsetGridLines) {
          valueOffset += (valueWidth / 2);
        }

        return Math.round(valueOffset);
      },
    });


    $("#groupSel").change(function(e){
        loadData();
    });

    $("#startWeekSel").change(function(e){
        loadData();

    });

    function findRate(rates, week){
        for(var i=0; i<rates.length; i++){
            var r = rates[i];
            if(r.week == week){
                return r.rate;
            }
        }

        return -1;
    }

    function loadData(){
        var group = $("#groupSel").val();
        var startWeek = $("#startWeekSel").val();
        var container = $("#data-container");

        $(container).text("");

        $.get('/api/1/reports/' + group + "/" + startWeek, function(r){
            if(!r.customers.length){
                $(container).text("No data found.");
                return;
            }

            var weeks = r.weeks;
            var rates_matrix = {};

            var html = '<table class="ntable" cellpadding="0" cellspacing="0">';
            html += '<tr class="head"><td>Customer</td>';

            for(var i=0; i<weeks.length; i++){
                html += '<td>' + weeks[i].name +'</td>';
            }

            html += '</tr>';

            for(var i=0; i<r.customers.length;i++){
                var customer = r.customers[i];
                html += '<tr><td>' + customer.name + '</td>';

                for(var j=0; j<weeks.length; j++){
                    var week_iso = weeks[j].iso;

                    var rate = findRate(customer.rates, week_iso);

                    if(!rates_matrix[week_iso]){
                        rates_matrix[week_iso] = [rate];
                    } else {
                        rates_matrix[week_iso].push(rate);
                    }

                    html += '<td>' + rate + '%</td>';
                }
                html += '</tr>'
            }
            html += '</table>';

            $(container).append(html);


            var data_x = [];
            var data_y = [];
            var data_y2 = [];

            for(var i=0; i<weeks.length; i++){
                data_x.push(weeks[i].name);

                var rates = rates_matrix[weeks[i].iso];
                var sum = 0;

                for(var j=0;j<rates.length;j++){
                    sum += rates[j];
                }

                if(sum <=1){
                    var avg = 0;
                } else {
                    var avg = parseInt(rates.length/sum * 100);
                }

                data_y.push(avg);
                data_y2.push(100);
            }

            buildChart(data_x, data_y, data_y2);

        });
    }

    function getChart(){
        $(chartContainer).empty();
        var  w = $(chartContainer).width();
        $(chartContainer).append("<canvas id='chartElm' height='400' width='"+ w +"'/>");
        return document.getElementById("chartElm").getContext("2d");
    }

    function buildChart(weeks, rates, defaults){


        var options = {
                bezierCurve: false,
                scaleShowGridLines : true,
                multiTooltipTemplate: "<%= datasetLabel %> <%= value %>%",
                scaleLabel: " <%=value%>%",
                scaleFontSize: 12,
            };

        var data = {
                labels: weeks,

                datasets: [
                    {
                        label: " ",
                        fillColor: "rgba(0,0,0,0.2)",
                        strokeColor: "rgba(0,0,0,1)",
                        pointColor: "rgba(0,0,0,1)",
                        pointStrokeColor: "#fff",
                        pointHighlightFill: "#fff",
                        pointHighlightStroke: "rgba(0,0,0,1)",
                        data: rates,
                    },
                    {
                        label: " ",
                        fillColor: "rgba(0,0,0,0.0)",
                        //fillColor: "rgba(114,190,73,0.2)",
                        strokeColor: "rgba(114,190,73,1)",
                        pointColor: "rgba(114,190,73,1)",
                        pointStrokeColor: "#fff",
                        pointHighlightFill: "#fff",
                        pointHighlightStroke: "rgba(114,190,73,1)",
                        data: defaults
                    }
                ]
            };

        var chart = new Chart(getChart()).Line(data, options);


    }

    loadData();

});