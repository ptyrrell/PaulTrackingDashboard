function getChart(element) {

    element.innerHTML = '';

    var id = element.getAttribute("id") + "_chart_elm";
    element.innerHTML = "<canvas id='" +  id + "' height='400' width='" + $(element).width() + "'/>";
    return document.getElementById(id).getContext("2d");
}

function buildChart(results) {

    var in_vals = [];
    var out_vals = [];
    var closing_balance = [];
    var available_credit = [];
    var x_weeks = [];

    var weeks = [];

    angular.forEach(results.data, function (value, week) {
        weeks.push(week);
    });

    weeks.sort();

    for (var i=0; i<weeks.length; i++){

        var value = results.data[weeks[i]];
        x_weeks.push(results.weeks[weeks[i]]);

        in_vals.push(value.cash_in);
        out_vals.push(value.cash_out);
        available_credit.push(value.available_credit);
        closing_balance.push(value.closing_balance);
    }

    var symbol = "$";

    var options = {
        bezierCurve: false,
        scaleShowGridLines: true,
        multiTooltipTemplate: "<%= datasetLabel %>: " + symbol + "<%= value %>",
        scaleLabel: " " + symbol + "<%=value%>",
        scaleFontSize: 12,
        animation: false,
    };

    var data = {
        labels: x_weeks,

        datasets: [
            {
                label: "Cash In",
                fillColor: "rgba(163,212,105,0.1)",
                strokeColor: "rgba(163,212,105,1)",
                pointColor: "rgba(163,212,105,1)",
                pointStrokeColor: "#fff",
                pointHighlightFill: "#fff",
                pointHighlightStroke: "rgba(163,212,105,1)",
                data: in_vals,
            },
            {
                label: "Cash Out",
                fillColor: "rgba(228,38,24,0.1)",
                strokeColor: "rgba(228,38,24,1)",
                pointColor: "rgba(228,38,24,1)",
                pointStrokeColor: "#fff",
                pointHighlightFill: "#fff",
                pointHighlightStroke: "rgba(228,38,24,1)",
                data: out_vals
            }
        ]
    };


    var data2 = {
        labels: x_weeks,

        datasets: [
            {
                type: "line",
                label: "Available Credit",
                fillColor: "rgba(255,255,255,0.0)",
                strokeColor: "rgba(169,75,121,1)",
                pointColor: "rgba(169,75,121,1)",
                pointStrokeColor: "#fff",
                pointHighlightFill: "#fff",
                pointHighlightStroke: "rgba(169,75,121,1)",
                data: available_credit,
            },
            {
                type: "bar",
                label: "Closing Bank Balance",
                fillColor: "rgba(98,150,199,0.1)",
                strokeColor: "rgba(98,150,199,1)",
                pointColor: "rgba(98,150,199,1)",
                pointStrokeColor: "#fff",
                pointHighlightFill: "#fff",
                pointHighlightStroke: "rgba(98,150,199,1)",
                data: closing_balance
            }
        ]
    };

    new Chart(getChart(document.getElementById("summaryChart"))).Overlay(data2, options);
    new Chart(getChart(document.getElementById("cashInOutChart"))).Bar(data, options);

}

var application = angular.module('knrgoals');

angular.forEach(["ui.sortable"], function (v) {
    application.requires.push(v);
});

application.controller("cashflow-controller", function ($scope, $http, $timeout) {

    var SUMMARY = "summary";
    var CASH_IN = "in";
    var CASH_OUT = "out";

    $scope.startWeek = null;
    $scope.endWeek = null;

    $scope.summaryData = null;
    $scope.cashData = null;
    $scope.activeCashType = SUMMARY;
    $scope.newDebtorName = null;
    $scope.addingDebtor = false;

    $scope.init = function (startWeek, endWeek) {
        // building summary
        $scope.startWeek = startWeek;
        $scope.endWeek = endWeek;

        $scope.loadSummaryData();
    };

    $scope.sortableOptions = {

        stop: function (e, ui) {
            $scope.saveOrder();
        }
    };

    $scope.loadSummaryData = function () {

        $scope.activeCashType = SUMMARY;

        $http({
            method: "GET",
            url: "/api/1/cashflow/summary?startWeek=" + $scope.startWeek + "&endWeek=" + $scope.endWeek
        }).then(function successCallback(response) {

            $scope.cashData = null;
            $scope.summaryData = response.data;

            // after rendering is complete
            $timeout(function() {
                buildChart(response.data);
            });

        }, function errorCallback(response) {
            alert("Error");
        });
    };

    $scope.getSummaryFieldTotal = function (fieldName) {

        let total = 0;

        if ($scope.summaryData) {
            angular.forEach($scope.summaryData.data, function (value, key) {
                total += value[fieldName];
            });
        }
        return total.toFixed(2);
    };

    $scope.getSummaryWeekField = function (weekId) {
        let data = $scope.summaryData.data[weekId];
        let total = 0;

        for (let key in data) {

           if (data.hasOwnProperty(key)) {

              total += data[key];
           }
        }

        return $scope.getNumberValue(total).toFixed(2);

    };

    $scope.cashKeypress = function (e, elm, debtor) {
        if (e.which === 13) {
            $scope.updateDebtor(elm, debtor);
        }
    };

    $scope.cashDataChange = function (elm, debtor) {
        elm.week.actual = elm.week.actual.replace(/[^0-9\.]/g, "");
        if (!elm.week.actual) {
            elm.week.actual = 0;
        }

        debtor.total = $scope.sumCashDebtor(debtor);

    };

    $scope.loadCashData = function (type) {

        $scope.activeCashType = type;

        $http({
            method: "GET",
            url: "/api/1/cashflow/" + type + "?startWeek=" + $scope.startWeek + "&endWeek=" + $scope.endWeek
        }).then(function successCallback(response) {

            var data = response.data;

            // building debtor total
            for (var i = 0; i < data.rows.length; i++) {
                data.rows[i].total = $scope.sumCashDebtor(data.rows[i]);
            }

            $scope.summaryData = null;
            $scope.cashData = data;

        }, function errorCallback(response) {
            alert("Error");
        });

    };

    $scope.sumCashDebtor = function (debtor) {

        var sum = 0.0;
        for (var i = 0; i < debtor.weeks.length; i++) {
            sum += $scope.getNumberValue(debtor.weeks[i].actual);
        }
        return sum.toFixed(2);
    };

    $scope.removeDebtor = function (debtor) {

        for (var i = 0; i < $scope.cashData.rows.length; i++) {

            var row = $scope.cashData.rows[i];

            if (row.id === debtor.id) {

                $scope.cashData.rows.splice(i, 1);

                $http({
                    method: "DELETE",
                    url: "/api/1/cashflow/" + $scope.activeCashType,
                    data: {"id": debtor.id}
                }).then(function successCallback(response) {

                }, function errorCallback() {
                    alert("Error");
                });
                break;
            }
        }
    };

    $scope.addNewDebtor = function () {

        if (!$scope.newDebtorName || $scope.addingDebtor) {
            return;
        }

        $scope.addingDebtor = true;

        var data = {
            "name": $scope.newDebtorName,
            "id": -1,
            "weeks": [],
            "total": $scope.getNumberValue(0.00).toFixed(2)
        };
        for (var i = 0; i < $scope.cashData.weeks.length; i++) {
            data.weeks.push({"week": $scope.cashData.weeks[i].iso, "actual": 0, "target": 0});
        }

        $http({
            method: "POST",
            url: "/api/1/cashflow/" + $scope.activeCashType,
            data: {"debtor": $scope.newDebtorName}
        }).then(function successCallback(response) {

            data["id"] = response.data.id;
            $scope.cashData.rows.push(data);

            $scope.saveOrder();

            $scope.addingDebtor = false;
        }, function errorCallback() {

            $scope.addingDebtor = false;
            alert("Error");
        });

        $scope.newDebtorName = "";
    };

    $scope.updateDebtor = function (elm, debtor) {

        $http({
            method: "PUT",
            url: "/api/1/cashflow/" + $scope.activeCashType,
            data: {"week": elm.week.week, "debtor": debtor.id, "value": $scope.getNumberValue(elm.week.actual)}
        }).then(function successCallback(response) {

        }, function errorCallback() {
            alert("Error");
        });
    };

    $scope.getNumberValue = function (num) {

        if (typeof num == "undefined" || num == null) {
            return num;
        }

        if (typeof num == 'string' || num instanceof String) {
            return (num.length > 0) ? parseFloat(num) : 0;
        }
        return num;
    };

    $scope.saveOrder = function () {

        var data = {};

        for (var i = 0; i < $scope.cashData.rows.length; i++) {
            data[$scope.cashData.rows[i]["id"]] = i;
        }

        $http({
            method: "POST",
            url: "/api/1/cashflow/order/" + $scope.activeCashType,
            data: {"data": data}
        }).then(function successCallback(response) {


        }, function errorCallback() {
            alert("Error");
        });

    }
});