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
            console.log('And now:');
            $.each(data, function (key, value) {
                var dataset = Array();
                dataset.push(value);
                console.log(value);
                options.series.push({'name': value['name'], 'data': value['data'], connectEnds: false});
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