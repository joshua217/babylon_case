import pandas as pd
from matplotlib import pyplot as plt
import numpy as np


if __name__ == "__main__":
    # File Paths
    data_1_path = r"C:\dev\data\josh-fyp\inputs\babylon\data_1.csv"
    data_2_path = r"C:\dev\data\josh-fyp\inputs\babylon\data_2.csv"

    # Read Data
    data_1 = pd.read_csv(data_1_path, parse_dates=['Period', 'Create time'])
    data_2 = pd.read_csv(data_2_path, parse_dates=['appt_date'])

    # Tidy
    data_1 = data_1.rename(columns={'Total time processing transaction':'Processing time', 'Total time on post processing':'Wrap-up time', 'IVR Treatment Time':'IVR treatment time'})  # Renaming columns for convenience
    data_1['Processing time'] = pd.to_timedelta(data_1['Processing time'])
    data_1['Wrap-up time'] = pd.to_timedelta((data_1['Wrap-up time']))
    data_1['IVR treatment time'] = pd.to_timedelta((data_1['IVR treatment time']))
    data_1 = data_1.dropna(subset=['Direction']) # Calls must have a direction, 1565 rows dropped
    data_1 = data_1[(data_1['Accept time'].notnull() | data_1['Abandon time'].notnull())] # Neither abandoned nor accepted, 14780 rows dropped, 81528 remaining
    data_1['result'] = 0    # Create result column where 0: abandoned call, 1: accepted call
    data_1.loc[data_1['Accept time'].notnull(), 'result'] = 1
    data_1['Create time'] = data_1['Create time'].replace(np.nan, 'replace')
    data_1 = data_1[data_1['Create time'] != 'replace'].copy()
    data_1['Create time'] = pd.to_datetime(data_1['Create time'], errors='coerce')
    data_1 = data_1.dropna(subset=['Create time'])

    # Examine within target period
    data_1 = data_1.loc[((data_1['Period'] >= '2019-2-1') & (data_1['Period'] <= '2019-4-27'))]




    print('Overall Abandonment Rate within Period:{} %'.format(round((len(data_1)-sum(data_1['result']))/len(data_1)*100), 2))

    # Examine Call Volume
    data_1['ones'] = 1
    data_1_grouped_sum = data_1.groupby(by=['Period']).sum().reset_index(drop=False)
    inb = data_1[data_1['Direction'] == 'inbound']
    inb = inb.groupby(by=['Period']).sum().reset_index(drop=False)
    out = data_1[data_1['Direction'] == 'outbound']
    out = out.groupby(by=['Period']).sum().reset_index(drop=False)
    # PLOT Call Volume
    plt.figure()
    plt.plot(data_1_grouped_sum['Period'], data_1_grouped_sum['ones'], label='Total Daily Calls')
    plt.plot(inb['Period'], inb['ones'], label='Inbound Calls')
    plt.plot(out['Period'], out['ones'], label='Outbound Calls')
    plt.xlabel('Period')
    plt.ylabel('Total Daily Calls')
    plt.title('Total Daily Calls across Period')
    plt.legend()
    plt.show()

    # Daily abandonment over time
    data_1_grouped = data_1.groupby(by=['Period']).mean().reset_index(drop=False)
    data_1_grouped['result'] = 1 - data_1_grouped['result']
    data_1_grouped['target'] = 0.1
    inb = data_1[data_1['Direction'] == 'inbound']
    inb = inb.groupby(by=['Period']).mean().reset_index(drop=False)
    inb['result'] = 1- inb['result']
    out = data_1[data_1['Direction'] == 'outbound']
    out = out.groupby(by=['Period']).mean().reset_index(drop=False)
    out['result'] = 1- out['result']

    # PLOT Abandonment Rate over the Period
    plt.figure()
    plt.plot(data_1_grouped['Period'], data_1_grouped['result'], label='Daily Abandonment %')
    plt.plot(data_1_grouped['Period'], data_1_grouped['target'], label='Target %')
    plt.plot(inb['Period'], inb['result'], label='Inbound Calls Abandonment %')
    plt.plot(out['Period'], out['result'], label='Outbound Calls Abandonment %')
    plt.xlabel('Period')
    plt.ylabel('Abandonment Rate')
    plt.title('Daily Abandonment Rate over Period')
    plt.legend()
    plt.show()

    # Now focus on Inbound calls
    inbound = data_1[data_1['Direction'] == 'inbound'].copy()
    inbound = inbound.dropna(subset=['Create time'])
    inbound['Abandon time'] = pd.to_datetime(inbound['Abandon time'], errors='coerce')
    inbound['Accept time'] = pd.to_datetime(inbound['Accept time'], errors='coerce')
    inbound['Wrap-up time'] = inbound['Wrap-up time'].fillna(pd.Timedelta(seconds=0))
    inbound['Processing time'] = inbound['Processing time'].fillna(pd.Timedelta(seconds=0))
    inbound['End time'] = (inbound['Accept time'] + inbound['Processing time'] + inbound['Wrap-up time'] + inbound['IVR treatment time'])
    inbound['End time'] = inbound['End time'].fillna(inbound['Abandon time'])
    inbound['Create time'] = pd.to_datetime(inbound['Create time'], errors='coerce')
    inbound = inbound.dropna(subset=['Create time'])
    inbound['IVR treatment time seconds'] = inbound['IVR treatment time'] / pd.to_timedelta(1, unit='S')

    # Profile Abandoned calls
    abandoned = inbound[inbound['Abandon time'].notnull()].copy()
    abandoned['Abandon time'] = pd.to_datetime(abandoned['Abandon time'], errors='coerce')
    abandoned = abandoned.dropna(subset=['Abandon time'])
    abandoned['Wait time'] = abandoned['Abandon time'] - abandoned['Create time']
    abandoned['Wait time seconds'] = abandoned['Wait time'] / pd.to_timedelta(1, unit='S')
    abandoned_grouped = abandoned.groupby(by=['Period']).mean().reset_index(drop=False)
    # Profile Accepted Calls
    accepted = inbound[inbound['Accept time'].notnull()].copy()
    accepted['IVR/Processing'] = accepted['IVR treatment time'] / accepted['Processing time']
    accepted['Accept time'] = pd.to_datetime(accepted['Accept time'], errors='coerce')
    accepted = accepted.dropna(subset=['Accept time'])
    accepted['Wait time'] = accepted['Accept time'] - accepted['Create time']
    accepted['Wait time seconds'] = accepted['Wait time'] / pd.to_timedelta(1, unit='S')
    accepted_grouped = accepted.groupby(by=['Period']).mean().reset_index(drop=False)

    # PLOT Histograms, Wait time of callers
    plt.figure()
    plt.hist(abandoned['Wait time seconds'], bins=100, alpha=0.5, color='blue')
    plt.xlabel('Time waited before abandoning call [seconds]')
    plt.ylabel('Number of calls')
    plt.title('Histogram of time waited before abandonment')
    plt.show()

    plt.figure()
    plt.hist(accepted['Wait time seconds'], bins=100, alpha=0.5, color='blue')
    plt.xlabel('Time waited before call is accepted [seconds]')
    plt.ylabel('Number of calls')
    plt.title('Histogram of time waited before call accepted')
    plt.show()

    # Examine Concurrent Calls
    create_events = inbound[['Create time', 'result']].copy()
    create_events['time'] = pd.to_datetime(create_events['Create time'], errors='coerce')
    create_events['time'] = create_events['time'].dropna()
    create_events['event_type'] = 1

    end_events = inbound[['End time', 'result']].copy()
    end_events['time'] = pd.to_datetime(end_events['End time'], errors='coerce')
    end_events['time'].dropna()
    end_events['event_type'] = -1

    events = pd.concat([create_events[['time', 'event_type', 'result']], end_events[['time', 'event_type', 'result']]])
    events = events.sort_values(by='time')

    events['concurrent_calls'] = events['event_type'].cumsum()
    events.insert(0, 'count', range(1, 1+len(events)))

    plt.figure()
    plt.plot(events['count'], events['concurrent_calls'], alpha=0.3)
    plt.xlabel('Time')
    plt.ylabel('Concurrent Calls')
    plt.xticks([])
    plt.title('Number of concurrent calls over time')
    plt.show()