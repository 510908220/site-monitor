# -*- encoding: utf-8 -*-

'''
数据导出封装
'''

import tablib


def excel(basic_info, records, file_path):
    title = '历史数据'
    data = tablib.Dataset(headers=['', '', '', '', '', '', ''], title=title)

    data.append_separator('--------------------------------------------------------------')
    data.append_separator('任务ID  {}'.format(basic_info['task_id']))
    data.append_separator('任务类型 {}'.format(basic_info['task_type']))
    data.append_separator('    站点 {}'.format(basic_info['url']))
    data.append_separator('时间范围 {} - {}'.format(basic_info['begin_date'], basic_info['end_date']))
    data.append_separator('--------------------------------------------------------------')
    data.append_separator('')

    data.append(['日期', '小时', '监测点', '平均响应时间', '可用率', '可用', '不可用'])
    for record in records:
        date, hour = record['update_time'].split(" ")
        data.append((date, hour, '平均', record['average_response_time'], record['availability'], record['ok'], record['bad']))
        for monitor_data in record['monitor_result_list']:
            data.append((date, hour, monitor_data['monitor_name'], monitor_data['tim'], '-', int(monitor_data['res']),  monitor_data['sta']))
        data.append_separator('')

    with open(file_path, "wb") as f:
        f.write(data.xls)
