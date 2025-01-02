#few_shots_1
#双向柱状图，可以是横轴双向，或者纵轴双向，双向柱状图可以清晰地展示两个相对数据系列之间的关系，必须是数据变化趋势截然相反的数据（如增长和减少）。这种对比可以帮助观察者识别趋势或差异。
#双向柱状图在视觉上是对称的，让数据解读性更强
from pyecharts import options as opts
from pyecharts.charts import Bar

# 新的数据
years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
#确保x轴的数据类型为字符串，否则会报错
years=[str(i) for i in years]
solar_capacity = [0.43, 0.77, 1.3, 1.74, 2.1, 2.53, 3.06, 4.3, 6.1]  # 单位：亿千瓦
wind_capacity = [1.45, 1.02, 0.98, 0.94, 0.89, 0.76, 0.63, 0.49, 0.35]  # 单位：亿千瓦

# 创建双向柱状图
bar = (
    Bar()
    .add_xaxis(years)
    .add_yaxis("太阳能容量（亿千瓦）", solar_capacity, stack="stack1", color="#675bba", 
                label_opts=opts.LabelOpts(is_show=True))  # 正向柱状图（带数据标签）
    .add_yaxis("风能容量（亿千瓦）", [-cap for cap in wind_capacity], stack="stack1", 
                color="#FF6F61", label_opts=opts.LabelOpts(is_show=True))  # 反向柱状图（带数据标签）
)

# 配置全局选项，添加图例
bar.set_global_opts(
    title_opts=opts.TitleOpts(title="太阳能与风能容量对比"),
    xaxis_opts=opts.AxisOpts(name="年份"),
    yaxis_opts=opts.AxisOpts(name="容量（亿千瓦）"),
    legend_opts=opts.LegendOpts(
        pos_top="top",  # 图例位置在顶部
        orient="horizontal"  # 水平排列
    ),
    tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
)

#保存为html文件，文件名为英文
bar.render("charts/engine_capacity_compare.html")

#few_shots_2

#组合图之双折线图，对于同一个事物或者关联的两个事物，两个角度下的数值变化
#例如：
#经济学中的经济总量和就业人数的双折线图
#人口数量和青年新婚率
#毕业生人数和报考研究生人数
#凡是有关联的两个事物，只要它们的数值在同一个时间区间变化，那么就可以用双折线图来表示。
from pyecharts import options as opts

from pyecharts.charts import Line, Grid
# 数据
#确保x轴的数据类型为字符串，否则会报错
years = ['2005', '2017', '2020', '2022', '2023', '2024', '2025']
years=[str(i) for i in years]
numbers = [117, 238, 341, 457, 474, 438, 388]
growth_rates = [0, 103.4, 43.2, 34.1, 3.7, -7.6, -10.5]  # 假设的增长率数据

# 创建考研报名人数折线图
line1 = (
    Line()
    .add_xaxis(years)
    .add_yaxis("考研报名人数（万）", numbers, markpoint_opts='x', is_smooth=True)
    .extend_axis(
        yaxis=opts.AxisOpts(
            name="增长率（%）",
            type_="value",
            min_=0,
            max_=100,
            position="right",
            axisline_opts=opts.AxisLineOpts(
                linestyle_opts=opts.LineStyleOpts(color="#675bba")
            ),
            axislabel_opts=opts.LabelOpts(formatter="{value} %"),
        )
    )
    .set_series_opts(label_opts=opts.LabelOpts(is_show=True))
)

# 创建增长率折线图
line2 = (
    Line()
    .add_xaxis(years[1:])  # 由于增长率数据从第二个年份开始，所以这里需要调整
    .add_yaxis("增长率（%）", growth_rates[1:], markpoint_opts="o", is_smooth=True)
    .set_series_opts(label_opts=opts.LabelOpts(is_show=True))
)

line1.overlap(line2)  # 叠加两个折线图

# 创建网格图
grid = (
    Grid()
   .add(line1, grid_opts=opts.GridOpts(pos_left="5%", pos_right="20%"))

)
#保存为html文件，文件名为英文
grid.render("echarts/two_lines_for_economics.html")

#few_shots_3

#组合图之一：条形图和折线图。常用于展示数据数值和其趋势变化用于辅助分析。例如总人数与增长或衰退率，总GDP和历年GDP增速等。
#当数值方差较大或者转折点多的时候，应使用条形图和折线图双图组合来呈现数据
from pyecharts import options as opts
from pyecharts.charts import Bar, Line, Grid

# 数据
#确保x轴的数据类型为字符串，否则会报错
years = ['2005', '2017', '2020', '2022', '2023', '2024', '2025']
years=[str(i) for i in years]
numbers = [117, 238, 341, 457, 474, 438, 388]  # 考研报名人数（单位：万）

# 计算增长率
growth_rates = [0]
for i in range(1, len(numbers)):
    growth_rates.append((numbers[i] - numbers[i - 1]) / numbers[i - 1] * 100)
bar = (
        Bar()
        .add_xaxis(years)
        .add_yaxis("考研报名人数（万）", numbers, color="#B0E0E6", yaxis_index=3)  # 报名人数使用浅蓝色
        .extend_axis(
            yaxis=opts.AxisOpts(
                name="增长率 (%)",
                type_="value",
                min_=int(min(growth_rates)-10),# 确保最小值能展示在图表当中，并腾出充足的空间
                max_=int(max(growth_rates)+10),  #确保最大值能展示在图表当中，并腾出充足的空间
                position="right",
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(color="#FF6F61")  # 增长率 Y轴线使用红色
                ),
                axislabel_opts=opts.LabelOpts(formatter="{value} %"),
                grid_index=0,
            )
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="考研报名人数与增长率示例"),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
        )
    )

line = (
        Line()
        .add_xaxis(years[1:])  # 从第二个年份开始
        .add_yaxis("增长率 (%)", growth_rates[1:], color="#FF6F61", yaxis_index=1)  # 增长率使用红色
        .set_global_opts(
            title_opts=opts.TitleOpts(title="考研报名人数增长率示例"),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
            yaxis_opts=opts.AxisOpts(name="增长率 (%)", min_=int(min(growth_rates)-10), max_=int(max(growth_rates)+10)),
        ))
bar.overlap(line)
grid=Grid().add(bar, opts.GridOpts(pos_left="5%", pos_right="20%"))
#保存为html文件，文件名为英文
grid.render("echarts/bar_line_for_numbers.html")

#few_shots_4

#三元时间序列图，当有三组相关联的数据在同一个时间轴或者x轴上存在序列时，可以使用三元时间序列图。
#三元时间序列图将两个量纲靠近的数据作为条形图并排显示，然后再用另一条折线表示剩下的那一个数据

def grid_mutil_yaxis() -> Grid:
    x_data = ["{}月".format(i) for i in range(1, 13)]
    bar = (
        Bar()
        .add_xaxis(x_data)
        .add_yaxis(
            "蒸发量",
            [2.0, 4.9, 7.0, 23.2, 25.6, 76.7, 135.6, 162.2, 32.6, 20.0, 6.4, 3.3],
            yaxis_index=0,
            color="#d14a61",
        )
        .add_yaxis(
            "降水量",
            [2.6, 5.9, 9.0, 26.4, 28.7, 70.7, 175.6, 182.2, 48.7, 18.8, 6.0, 2.3],
            yaxis_index=1,
            color="#5793f3",
        )
        .extend_axis(
            yaxis=opts.AxisOpts(
                name="蒸发量",
                type_="value",
                min_=0,
                max_=250,
                position="right",
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(color="#d14a61")
                ),
                axislabel_opts=opts.LabelOpts(formatter="{value} ml"),
            )
        )
        .extend_axis(
            yaxis=opts.AxisOpts(
                type_="value",
                name="温度",
                min_=0,
                max_=25,
                position="left",
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(color="#675bba")
                ),
                axislabel_opts=opts.LabelOpts(formatter="{value} °C"),
                splitline_opts=opts.SplitLineOpts(
                    is_show=True, linestyle_opts=opts.LineStyleOpts(opacity=1)
                ),
            )
        )
        .set_global_opts(
            yaxis_opts=opts.AxisOpts(
                name="降水量",
                min_=0,
                max_=250,
                position="right",
                offset=80,
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(color="#5793f3")
                ),
                axislabel_opts=opts.LabelOpts(formatter="{value} ml"),
            ),
            title_opts=opts.TitleOpts(title="Grid-多 Y 轴示例"),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
        )
    )

    line = (
        Line()
        .add_xaxis(x_data)
        .add_yaxis(
            "平均温度",
            [2.0, 2.2, 3.3, 4.5, 6.3, 10.2, 20.3, 23.4, 23.0, 16.5, 12.0, 6.2],
            yaxis_index=2,
            color="#675bba",
            label_opts=opts.LabelOpts(is_show=False),
        )
    )

    bar.overlap(line)
    return Grid().add(
        bar, opts.GridOpts(pos_left="5%", pos_right="20%")
    )

bar=grid_mutil_yaxis()
#保存为html文件，文件名为英文
bar.render("echarts/grid_mutil_yaxis.html")

#few_shots_5
from pyecharts import options as opts 
from pyecharts.charts import Bar, Line, Grid 
#确保x轴的数据类型为字符串，否则会报错
years = ['2005', '2017', '2020', '2022', '2023', '2024', '2025'] 
years=[str(i) for i in years]
numbers = [117, 238, 341, 457, 474, 438, 388] # 考研报名人数（单位：万）
growth_rates=[]
for i in range(1, len(numbers)):
    growth_rates.append((numbers[i]-numbers[i-1])/(numbers[i-1]+1e-10)*100) #eps防止除零错误
bar = (Bar() .add_xaxis(years) .add_yaxis("报名人数（万）", numbers, color="#00509E", category_gap="50%") .set_series_opts(label_opts=opts.LabelOpts(is_show=True)) # 显示数据标签 
) 
line = ( Line() .add_xaxis(years[1:]) .add_yaxis("增长率（%）", growth_rates[1:], color="#FF6F61", is_smooth=True, markpoint_opts=opts.MarkPointOpts( data=[opts.MarkPointItem(type_="max"), opts.MarkPointItem(type_="min")], label_opts=opts.LabelOpts(position="top") 
                                                                                                                                                # 设置标记点标签位置 
                                                                                                    ), yaxis_index=1 
                                                                                                    
                                        # 使折线图使用右侧 Y 轴 
                            ) ) 
# 合并图像 
grid = ( Grid() .add(bar, grid_opts=opts.GridOpts(pos_left="5%", pos_right="20%")) .add(line, grid_opts=opts.GridOpts(pos_left="5%", pos_right="20%", pos_top="70%")) )
grid.render_notebook()

#few_shots_6
# 创建玫瑰图，玫瑰图可以突出显示某个数据项的大小，并通过半径大小区分数据占比，用于确定数据集中占比最大的项或者是感兴趣的项在数据集中的占比直观体现
#确定图表类型：玫瑰图
from pyecharts import options as opts
from pyecharts.charts import Pie
# 设计数据
labels = ['考研', '就业', '考公', '出国留学']
sizes = [20, 60, 20, 10]
colors = ['#FF9999', '#66B3FF', '#99FF99', '#FFCC99']  # 颜色设置
rose_chart = (
    Pie()
    .add("", [list(z) for z in zip(labels, sizes)], radius=["30%", "75%"], rosetype="radius")  # 设置 rosetype 为 "radius"
    .set_colors(colors)
    .set_global_opts(title_opts=opts.TitleOpts(title="2023年大学生总人数分布（734万人）", subtitle="各个类别的占比"),
                     legend_opts=opts.LegendOpts(orient="vertical", pos_left="left", pos_top="middle"))
    .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c} ({d}%)"))  # 设置标签格式
)

#保存为html文件,文件名为英文
rose_chart.render("charts/2023_the_number_of_students_in_university_chart.html")
#图表将会转化为url: http://localhost:6300/charts/2023_the_number_of_students_in_university_chart.html

#few_shots_7
#饼状图用于展示各个类别的比例，提供全局视角，适合想多方了解的用户
#选择图表类型：饼状图
from pyecharts import options as opts
from pyecharts.charts import Pie
# 数据
#确保数据类型为字符串，否则会报错
labels = ['考研', '就业', '考公', '出国留学']
labels=[ str(i) for i in labels]
sizes = [20, 60, 20, 10]
colors = ['#FF9999', '#66B3FF', '#99FF99', '#FFCC99']  # 颜色设置

# 创建饼状图
pie_chart = (
    Pie()
    .add("", [list(z) for z in zip(labels, sizes)], radius=["30%", "75%"])  # 定义内外半径
    .set_colors(colors)
    .set_global_opts(title_opts=opts.TitleOpts(title="2023年大学生总人数分布（734万人）", subtitle="各个类别的占比"),
                     legend_opts=opts.LegendOpts(orient="vertical", pos_left="left", pos_top="middle"))
    .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c} ({d}%)"))  # 设置标签格式
)

# 保存为html文件,文件名为英文
pie_chart.render("charts/2023_the_number_of_students_in_university_chart.html")
#图表将会转化为url: http://localhost:6300/charts/2023_the_number_of_students_in_university_chart.html

#基本折线图，用于展示时间序列数据的按照时间变化趋势，常用于时间序列数据分析，趋势分析和未来趋势预测、历史趋势总结
from pyecharts import options as opts
from pyecharts.charts import Line
# 数据
#确保即将成为x轴坐标的数据类型为字符串，否则会报错
years = ['2005', '2017', '2020', '2022', '2023', '2024', '2025']
years=[str(i) for i in years]
numbers = [117, 238, 341, 457, 474, 438, 388]
# 创建折线图实例
line_chart = (
    Line()
    .add_xaxis(years)  # 添加 x 轴数据
    .add_yaxis("考研报名人数（万）", numbers, is_smooth=True, 
                markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max"), opts.MarkPointItem(type_="min")]), #显示出折线图的最大值和最小值，让数据表现有侧重点
                color="#FF5733")  # 添加 y 轴数据
    .set_series_opts(label_opts=opts.LabelOpts(is_show=True))  # 显示数据点
    .set_global_opts(
        title_opts=opts.TitleOpts(title="历年考研报名人数"),
        yaxis_opts=opts.AxisOpts(name="考研报名人数（万）", position="left"),
    )
)
#保存为html文件,文件名为英文
line_chart.render("charts/2023_the_number_of_students_in_university_chart.html")
#图表将会转化为url: http://localhost:6300/charts/2023_the_number_of_students_in_university_chart.html
# 创建水球图的代码
from pyecharts import options as opts
from pyecharts.charts import Liquid

# 数据
v1 = 0.5
v2 = 0.3
v3 = 0.2
v4 = 0.1

# 创建水球图实例
c = (
    Liquid()
    .add("完成率", [0.5], is_outline_show=False, color=['#DC143C'])
    .set_global_opts(title_opts=opts.TitleOpts(title="XX业务完成情况", pos_left="center"))
)
# 保存为html文件,文件名为英文
c.render("charts/liquid_chart.html")
#图表将会转化为url: http://localhost:6300/charts/liquid_chart.html


#动态时间轴饼图，适合时间序列数据或者多个类别数据的份额变化，如N个公司年销售额变化量、N个市场月订单量变化。
#多个个体+时间动态变化数据，可使用时间轴饼图增强视觉体验。
from pyecharts import options as opts
from pyecharts.charts import Pie, Timeline
# 销售额属性
attr = ["手机", "电脑", "平板", "电视", "配件"]

# 根据参考信息构造每年的销售数据
sales_data = {
    2015: [300, 200, 150, 100, 50],
    2016: [400, 250, 200, 150, 75],
    2017: [450, 300, 250, 200, 100],
    2018: [500, 350, 300, 250, 150],
    2019: [550, 400, 350, 300, 200]
}

# 创建时间线对象
tl = Timeline()
# 设置时间线的自动播放和时间间隔
tl.add_schema(
    is_auto_play=True,
    play_interval=1000,  # 每隔1000毫秒播放一次
    pos_bottom="0%",
    axis_type="category"
)
# 生成 2015 到 2019 年的数据
for year in range(2015, 2020):
    pie = (
        Pie()
        .add(
            "Shop A",  # 饼图名称
            [list(z) for z in zip(attr, sales_data[year])],  # 数据源
            rosetype="radius",  # 饼图类型
            radius=["30%", "55%"],  # 饼图半径
        )
        .set_global_opts(title_opts=opts.TitleOpts("{} 年销售额".format(year)))  # 设置标题
    )
    tl.add(pie, "{} 年".format(year))  # 将饼图添加到时间线


# 保存为html文件,文件名为英文
tl.render("charts/timeline_pie_chart.html")
#图表将会转化为url: http://localhost:6300/charts/timeline_pie_chart.html

#时间轴折线图，适合于有多个年份，多个个体的变化数据，当数据量较多时，可以用时间轴来展示不同类别的数据在不同年份变化的趋势。
from pyecharts import options as opts
from pyecharts.charts import Pie, Timeline, Line

# 销售额属性
attr = ["手机", "电脑", "平板", "电视", "配件"]

# 根据参考信息构造每年的销售数据
sales_data = {
    2015: [300, 200, 150, 100, 50],
    2016: [400, 250, 200, 150, 75],
    2017: [450, 300, 250, 200, 100],
    2018: [500, 350, 300, 250, 150],
    2019: [550, 400, 350, 300, 200]
}

# 创建时间线对象
tl = Timeline()

# 设置时间线的自动播放和时间间隔
tl.add_schema(
    is_auto_play=True,
    play_interval=5000,  # 每隔1000毫秒播放一次
    pos_bottom="0%",
    axis_type="category"
)

# 生成 2015 到 2019 年的数据
for year in range(2015, 2020):
    # 创建饼图
    pie = (
        Pie()
        .add(
            "Shop A",  # 饼图名称
            [list(z) for z in zip(attr, sales_data[year])],  # 数据源
            rosetype="radius",  # 饼图类型
            radius=["30%", "55%"],  # 饼图半径
        )
        .set_global_opts(title_opts=opts.TitleOpts("{} 年销售额".format(year)))  # 设置标题
    )
    
    # 添加折线图
    line = (
        Line()
        .add_xaxis([str(y) for y in range(2015, 2020)])  # x轴为年份
        .add_yaxis("销售额", [sum(sales_data[y]) for y in range(2015, year + 1)], 
                   is_smooth=True,markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max",name="最大值")]),)
        .set_global_opts(
            title_opts=opts.TitleOpts("{} 年销售额变化".format(year)),
            yaxis_opts=opts.AxisOpts(name="销售额"),
            xaxis_opts=opts.AxisOpts(name="年份"),
        )
    )
    
    # 将饼图和折线图添加到时间线
    tl.add(pie, "{} 年".format(year))  # 饼图
    tl.add(line, "{} 年".format(year))  # 折线图

# 保存为html文件,文件名为英文
tl.render("charts/timeline_line_chart.html")
#图表将会转化为url: http://localhost:6300/charts/timeline_line_chart.html

