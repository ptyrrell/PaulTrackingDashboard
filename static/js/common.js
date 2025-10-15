var KNRCommon = {

    build_simple_chart: function (chart_id, weeks, line_1_values, line_1_name, line_2_values, line_2_name, symbol) {

        if (!symbol) {
            symbol = "$";
        }

        function getChart() {
            $(chart_id).empty();
            var w = $(chart_id).width();
            $(chart_id).append("<canvas id='chartElm' height='400' width='" + w + "'/>");

            return document.getElementById("chartElm").getContext("2d");
        }

        var options = {
            bezierCurve: false,
            scaleShowGridLines: true,
            multiTooltipTemplate: "<%= datasetLabel %>: " + symbol + "<%= value %>",
            scaleLabel: " " + symbol + "<%=value%>",
            scaleFontSize: 12,
            animation: false
        };

        var data = {
            labels: weeks,

            datasets: [
                {
                    type: "line",
                    label: line_1_name,
                    fillColor: "rgba(255,255,255,0.0)",
                    strokeColor: "rgba(169,75,121,1)",
                    pointColor: "rgba(169,75,121,1)",
                    pointStrokeColor: "#fff",
                    pointHighlightFill: "#fff",
                    pointHighlightStroke: "rgba(169,75,121,1)",
                    data: line_1_values
                },
                {
                    type: "line",
                    label: line_2_name,
                    fillColor: "rgba(98,150,199,0.1)",
                    strokeColor: "rgba(98,150,199,1)",
                    pointColor: "rgba(98,150,199,1)",
                    pointStrokeColor: "#fff",
                    pointHighlightFill: "#fff",
                    pointHighlightStroke: "rgba(98,150,199,1)",
                    data: line_2_values
                }
            ]
        };
        var chart = new Chart(getChart()).Line(data, options);

    }
};

$(function(){

        setTimeout(function() {
            $('.alert-dismissible').fadeOut('fast');
        }, 3000);

});