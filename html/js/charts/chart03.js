$(function () {

    $(document).ready(function () {

        var options = {
            chart: {
                plotBackgroundColor: null,
                plotBorderWidth: null,
                plotShadow: false,
                type: 'line',
                renderTo: 'post-history',
                height: 300
            },
            title: {
                text: ''
            },
            navigator : {
                enabled : false
            },
            rangeSelector : {
                selected : 1
            },
            xAxis: {
              type: 'datetime',
              dateTimeLabelFormats: {
                  month: '%e. %b',
                  year: '%b'
              }
            },
            plotOptions: {
                spline: {
                    allowPointSelect: true,
                    cursor: 'pointer',
                    dataLabels: {
                        enabled: false
                    },
                    showInLegend: false
                }
            },
            credits: {
                enabled: false
            },
            series: [{}]
        };



        $.getJSON('./_data/post_history.json', function (data) {
            $.each(data, function (key, value) {
                options.series.push({'name': value['name'], 'data': value['data'], connectEnds: false});
            });
            var chart = new Highcharts.StockChart(options);
        });

    });
});