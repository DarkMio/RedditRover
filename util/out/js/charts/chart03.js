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
            tooltip: {
                pointFormat: '<b>{point.y:.f} submissions</b>'
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



        $.getJSON('post_history.json', function (data) {
            console.log('And now:');
            $.each(data, function (key, value) {
                var dataset = Array();
                for(var point in value['data']) {
                    var time = value['data'][point];
                    dataset.push([time, 1]);
                }
                options.series.push({'name': value['name'], 'data': dataset, dataGrouping: {approximation: "sum"}
                });
            });
            console.log(options.series);
            var chart = new Highcharts.StockChart(options);
        });

    });
});


/*        $.getJSON('post_history.json', function (data) {
            $.each(data, function (key, value) {
                if (key == 'JiffierBot') {
                    $.each(value, function(k, v) {
                        JB.data.push(v);
                    })
                } else if (key == 'SmallSubBot') {
                    $.each(value, function(k, v) {
                        SSB.data.push(v);
                    })
                }
            });
            console.log(data);
            options.series.push(JB, SSB);
            console.log(options.series);
            var chart = new Highcharts.Chart(options);
        });

    });
});
*/