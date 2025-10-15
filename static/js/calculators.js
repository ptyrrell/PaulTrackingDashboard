$(function(){

    $(".input-numeric").keydown(function (e) {
        // Allow: backspace, delete, tab, escape, enter and .
        if ($.inArray(e.keyCode, [46, 8, 9, 27, 13, 110, 190]) !== -1 ||
             // Allow: Ctrl+A
            (e.keyCode == 65 && e.ctrlKey === true) ||
             // Allow: Ctrl+C
            (e.keyCode == 67 && e.ctrlKey === true) ||
             // Allow: Ctrl+X
            (e.keyCode == 88 && e.ctrlKey === true) ||
             // Allow: home, end, left, right
            (e.keyCode >= 35 && e.keyCode <= 39)) {
                 // let it happen, don't do anything
                 return;
        }
        // Ensure that it is a number and stop the keypress
        if ((e.shiftKey || (e.keyCode < 48 || e.keyCode > 57)) && (e.keyCode < 96 || e.keyCode > 105)) {
            e.preventDefault();
        }
    });

    $(".btn-reset").click(function(){
        $(".input-numeric").val("0");
        $(".calc-result").empty();


        //var vals = $(this).attr("data-cls").split(",");
        //for(var i=0; i<vals.length; i++){
        //    $("input[name=" + vals[i] + "]").val("0");
        //}
    });


    $(".calc-a").click(function(){
        $(".calc-result").empty();
        $(".calc").addClass("hidden");

        var cl = $($(this).attr("data-sel"));
        $(cl).removeClass("hidden");

    });

    function process_number(n){
        if(isNaN(n) || !isFinite(n)){
            return 0;
        }

        if (n === parseInt(n, 10))
            return n;
        else
            // love js
            return Number(Number(n).toFixed(2));
    }

    function snum(sel){
        var s = $(sel);
        if(!s.length){
            s = $("input[name=" + sel + "]");
        }

        if(s.hasClass("input-numeric")){
            return process_number($(s).val());
        }
        return process_number($(s).text());
    }


    function generateByWeekTable(){
        var be = process_number($(".be-result").text());
        var gogs_val = Number($("input[name=breakeven-v5]").val());
        var monthly_exp = Number($("input[name=breakeven-v1]").val());
        var g_wages = Number($("input[name=breakeven-v2]").val());
        var super_a = Number($("input[name=breakeven-v3]").val());

        var wt1ps = snum("wt1-ps");
        var wt2ps = snum("wt2-ps");
        var wt3ps = snum("wt3-ps");
        var wt4ps = snum("wt4-ps");

        var wt1a = snum("wt1-a");
        var wt2a = snum("wt2-a");
        var wt3a = snum("wt3-a");
        var wt4a = snum("wt4-a");

        var wt1bi = process_number(be * (wt1ps / 100.0));
        var wt2bi = process_number(be * (wt2ps / 100.0));
        var wt3bi = process_number(be * (wt3ps / 100.0));
        var wt4bi = process_number(be * (wt4ps / 100.0));

        var wt1diff = process_number(wt1a - wt1bi);
        var wt2diff = process_number(wt2a - wt2bi);
        var wt3diff = process_number(wt3a - wt3bi);
        var wt4diff = process_number(wt4a - wt4bi);

        // Filling
        $(".wt1-bi").text(wt1bi);
        $(".wt2-bi").text(wt2bi);
        $(".wt3-bi").text(wt3bi);
        $(".wt4-bi").text(wt4bi);

        $(".wt1-diff").text(wt1diff);
        $(".wt2-diff").text(wt2diff);
        $(".wt3-diff").text(wt3diff);
        $(".wt4-diff").text(wt4diff);

        var total_bi = process_number(wt1bi + wt2bi + wt3bi + wt4bi);

        $(".wtm-ps").text(process_number(wt1ps + wt2ps + wt3ps + wt4ps));
        $(".wtm-bi").text(total_bi);
        $(".wtm-a").text(wt1a + wt2a + wt3a + wt4a);
        $(".wtm-diff").text(process_number(snum(".wtm-a") - snum(".wtm-bi")));

        // Gogs table
        var gogs1 = process_number(gogs_val/100.0 * wt1bi);
        var gogs2 = process_number(gogs_val/100.0 * wt2bi);
        var gogs3 = process_number(gogs_val/100.0 * wt3bi);
        var gogs4 = process_number(gogs_val/100.0 * wt4bi);

        var gogs1a = snum("gogs1-a");
        var gogs2a = snum("gogs2-a");
        var gogs3a = snum("gogs3-a");
        var gogs4a = snum("gogs4-a");

        var gogs1diff = gogs1a - gogs1;
        var gogs2diff = gogs2a - gogs2;
        var gogs3diff = gogs3a - gogs3;
        var gogs4diff = gogs4a - gogs4;


        $(".gogs1").text(gogs1);
        $(".gogs2").text(gogs2);
        $(".gogs3").text(gogs3);
        $(".gogs4").text(gogs4);

        $(".gogs1-diff").text(gogs1diff);
        $(".gogs2-diff").text(gogs2diff);
        $(".gogs3-diff").text(gogs3diff);
        $(".gogs4-diff").text(gogs4diff);

        var total_gogs = gogs1 + gogs2 + gogs3 + gogs4;

        $(".mgogs").text(total_gogs);
        $(".mgogs-a").text(gogs1a + gogs2a + gogs3a + gogs4a);
        $(".mgogs-diff").text(gogs1diff + gogs2diff + gogs3diff + gogs4diff);

        $(".pl-sales").text(total_bi);
        $(".pl-gogs").text(total_gogs);
        $(".pl-gprofit").text(process_number(total_bi - total_gogs));
        $(".pl-exp").text(monthly_exp);
        $(".pl-wages").text(g_wages);
        $(".pl-sup").text(super_a);
        $(".pl-profit").text( process_number(total_bi - total_gogs -  monthly_exp - g_wages - super_a));
    }

    $("input.wt").keyup(function (e) {
        if (e.keyCode == 13) {
            generateByWeekTable();
        }
    });


    // Breakeven Analyser
    $(".breakeven-btn").click(function(){
        var num1 = Number($("input[name=breakeven-v1]").val());
        var num2 = Number($("input[name=breakeven-v2]").val());
        var num3 = Number($("input[name=breakeven-v3]").val());
        var num4 = Number($("input[name=breakeven-v4]").val());
        var num5 = Number($("input[name=breakeven-v5]").val());
        var num6 = Number($("input[name=breakeven-v6]").val());

        if(!num3) {
            num3 = num2 * 0.095;
        }
        if(!num6){
            num6 = 100 - num5;
        }
        var r = process_number( (num1 + num2 + num3 + num4) / (num6/100.0) );
        $(".breakeven-result").html("Break even income: <span class='be-result'>" + r + "</span> $");

        $("input[name=wt1-ps]").val(25);
        $("input[name=wt2-ps]").val(25);
        $("input[name=wt3-ps]").val(25);
        $("input[name=wt4-ps]").val(25);

        $("input[name=wt1-a]").val(0);
        $("input[name=wt2-a]").val(0);
        $("input[name=wt3-a]").val(0);
        $("input[name=wt4-a]").val(0);

        $("input[name=gogs1-a]").val(0);
        $("input[name=gogs2-a]").val(0);
        $("input[name=gogs3-a]").val(0);
        $("input[name=gogs4-a]").val(0);

        generateByWeekTable();

    });


    // Debt ratio
    $(".debt-ratio-btn").click(function(){
        var num1 = $("input[name=debt-ratio-ass-am]").val();
        var num2 = $("input[name=debt-ratio-lia-am]").val();

        var r = process_number((Number(num2)/Number(num1)) * 100);
        $(".debt-ratio-result").html("Debt ratio " + r + "%");

    });

    // Debt to income ratio

    $(".debt-income-ratio-btn").click(function(){
        var num1 = Number($("input[name=debt-inc1]").val());
        var num2 = Number($("input[name=debt-inc2]").val());
        var num3 = Number($("input[name=debt-inc3]").val());

        var r = process_number(num3/(num1 + num2));
        $(".debt-income-ratio-result").html("Debt to Income Ratio " + r + " : 1");

    });


    // Interest Cover

    $(".inc-cv-btn").click(function(){
        var num1 = Number($("input[name=inc-cv1]").val());
        var num2 = Number($("input[name=inc-cv2]").val());
        var num3 = Number($("input[name=inc-cv3]").val());

        var r = process_number((num3 + num1 + num2)/(num1 + num2));
        $(".inc-cv-result").html("Interest Cover Ratio " + r + " : 1");
    });


    // Net Margin

    $(".net-margin-btn").click(function(){
        var num1 = Number($("input[name=net-m1]").val());
        var num2 = Number($("input[name=net-m2]").val());

        var r = process_number((num2/num1) * 100);
        $(".net-margin-result").html("Net Profit Margin " + r + "%");
    });

    // Gross Margin

    $(".gross-margin-btn").click(function(){
        var num1 = Number($("input[name=gross-m1]").val());
        var num2 = Number($("input[name=gross-m2]").val());

        var r = process_number((num2/num1) * 100);
        $(".gross-margin-result").html("Gross Profit Margin " + r + "%");
    });

    // Return on assets

    $(".return-btn").click(function(){
        var num1 = Number($("input[name=return-v1]").val());
        var num2 = Number($("input[name=return-v2]").val());

        var r = process_number((num1/num2) * 100);
        $(".return-result").html("Return on Assets " + r + "%");
    });

    // Operating Expenses to Sales
    $(".operating-btn").click(function(){
        var num1 = Number($("input[name=operating-v1]").val());
        var num2 = Number($("input[name=operating-v2]").val());
        var num3 = Number($("input[name=operating-v3]").val());
        var num4 = Number($("input[name=operating-v4]").val());
        var num5 = Number($("input[name=operating-v5]").val());
        var num6 = Number($("input[name=operating-v6]").val());

        var r = process_number(((num2 + num6 - (num4 + num5 + num3))/num1) * 100);
        $(".operating-result").html("Operating Expenses to Sales " + r + "%");
    });


    // Sales per employee
    $(".sales-emp-btn").click(function(){
        var num1 = Number($("input[name=sales-emp-v1]").val());
        var num2 = Number($("input[name=sales-emp-v2]").val());
        var num3 = Number($("input[name=sales-emp-v3]").val());
        var num4 = Number($("input[name=sales-emp-v4]").val());
        var num5 = Number($("input[name=sales-emp-v5]").val());

        var r2 = num2 + num5 + process_number((num4 * num3)/40);
        var r = process_number( num1/r2 );
        $(".sales-emp-result").html("Sales per Full Time Equivalent $" + r + "<br>Number of Full Time Equivalents " + r2);
    });

    // Working Capital
    $(".working-btn").click(function(){
        var num1 = Number($("input[name=working-v1]").val());
        var num2 = Number($("input[name=working-v2]").val());

        var r = process_number(num1/num2);
        $(".working-result").html("Working Capital Ratio " + r + " : 1");
    });


    // Quick Assets Ratio
    $(".quick-btn").click(function(){
        var num1 = Number($("input[name=quick-v1]").val());
        var num2 = Number($("input[name=quick-v2]").val());
        var num3 = Number($("input[name=quick-v3]").val());

        var r = process_number( (num2 - num1)/num3 );
        $(".quick-result").html("Quick Assets Ratio " + r + " : 1 %");
    });

    // Stock Turnover
    $(".stock-btn").click(function(){
        var num1 = Number($("input[name=stock-v1]").val());
        var num2 = Number($("input[name=stock-v2]").val());
        var num3 = Number($("input[name=stock-v3]").val());

        var r = process_number( num1/((num2 + num3)/2) );
        $(".stock-result").html("Stock Turnover Ratio " + r + " times");
    });

    // Debtor Ageing Ratio
    $(".debtor-btn").click(function(){
        var num1 = Number($("input[name=debtor-v1]").val());
        var num2 = Number($("input[name=debtor-v2]").val());

        var r = process_number( (num1/num2) * 365 );
        $(".debtor-result").html("Debtor Ageing Ratio " + r + " days");
    });

    // Creditor Ageing Ratio
    $(".creditor-btn").click(function(){
        var num1 = Number($("input[name=creditor-v1]").val());
        var num2 = Number($("input[name=creditor-v2]").val());

        var r = process_number( (num1/num2) * 365 );
        $(".creditor-result").html("Creditor Ageing Ratio " + r + " days");
    });

    $(".calc").addClass("hidden");
    $(".calc").first().removeClass("hidden");

});
