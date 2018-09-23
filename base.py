import sys
import pandas as pd
import numpy as np
import random
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from matplotlib import pyplot as plt
import len, range


def get_grouped_data(input_data, feature, target_col, bins, cuts=0):
    has_null = pd.isnull(input_data[feature]).sum() > 0
    if has_null == 1:
        data_null = input_data[pd.isnull(input_data[feature])]
        input_data = input_data[~pd.isnull(input_data[feature])]
        input_data.reset_index(inplace=True, drop=True)

    is_train = 0
    if cuts == 0:
        is_train = 1
        prev_cut = min(input_data[feature]) - 1
        cuts = [prev_cut]
        reduced_cuts = 0
        for i in range(1, bins + 1):
            next_cut = np.percentile(input_data[feature], i * 100.0 / bins)
            if next_cut != prev_cut:
                cuts.append(next_cut)
            else:
                reduced_cuts = reduced_cuts + 1
            prev_cut = next_cut

        if reduced_cuts > 0:
            print('Reduced the number of bins due to less variation in feature')
        cut_series = pd.cut(input_data[feature], cuts)
    else:
        cut_series = pd.cut(input_data[feature], cuts)

    grouped = input_data.groupby([cut_series], as_index=True).agg(
        {target_col: [np.size, np.mean], feature: [np.mean]})
    grouped.columns = ['_'.join(cols).strip() for cols in grouped.columns.values]
    grouped[grouped.index.name] = grouped.index
    grouped.reset_index(inplace=True, drop=True)
    grouped = grouped[[feature] + list(grouped.columns[0:3])]
    grouped = grouped.rename(index=str, columns={target_col + '_size': 'Samples_in_bin'})
    grouped = grouped.reset_index(drop=True)
    corrected_bin_name = '[' + str(min(input_data[feature])) + ', ' + str(grouped.loc[0, feature]).split(',')[1]
    grouped[feature] = grouped[feature].astype('category')
    grouped[feature] = grouped[feature].cat.add_categories(corrected_bin_name)
    grouped.loc[0, feature] = corrected_bin_name

    if has_null == 1:
        grouped_null = grouped.loc[0:0, :].copy()
        grouped_null[feature] = grouped_null[feature].astype('category')
        grouped_null[feature] = grouped_null[feature].cat.add_categories('Nulls')
        grouped_null.loc[0, feature] = 'Nulls'
        grouped_null.loc[0, 'Samples_in_bin'] = len(data_null)
        grouped_null.loc[0, target_col + '_mean'] = data_null[target_col].mean()
        grouped_null.loc[0, feature + '_mean'] = np.nan
        grouped[feature] = grouped[feature].astype('str')
        grouped = pd.concat([grouped_null, grouped], axis=0)
        grouped.reset_index(inplace=True, drop=True)

    grouped[feature] = grouped[feature].astype('str').astype('category')
    if is_train == 1:
        return (cuts, grouped)
    else:
        return (grouped)


def draw_plots_old(input_data, feature, target_col, trend_correlation=None):
    trend_changes = get_trend_changes(grouped_data=input_data, feature=feature, target_col=target_col)
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(input_data[target_col + '_mean'], marker='o')
    plt.xticks(np.arange(len(input_data)), (input_data[feature]).astype('str'), rotation=45)
    plt.xlabel('Bins of ' + feature)
    plt.ylabel('Average of ' + target_col)
    comment = "Trend changed " + str(trend_changes) + " times"
    if trend_correlation != None:
        comment = comment + '\n' + 'Correlation with train trend: ' + str(int(trend_correlation * 100))
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.6)
    plt.text(0.2, 0.48, comment, fontsize=14, verticalalignment='top', bbox=props)
    plt.title('Average of ' + target_col + ' wrt ' + feature)
    plt.subplot(1, 2, 2)
    plt.bar(np.arange(len(input_data)), input_data['Samples_in_bin'], alpha=0.5)
    plt.xticks(np.arange(len(input_data)), (input_data[feature]).astype('str'), rotation=45)
    plt.xlabel('Bins of ' + feature)
    plt.ylabel('Bin-wise sample size')
    plt.title('Samples in bins of ' + feature)
    plt.tight_layout()
    plt.show()


def draw_plots(input_data, feature, target_col, trend_correlation=None):
    trend_changes = get_trend_changes(grouped_data=input_data, feature=feature, target_col=target_col)
    plt.figure(figsize=(12, 5))
    ax1 = plt.subplot(1, 2, 1)
    ax1.plot(input_data[target_col + '_mean'], marker='o')
    ax1.set_xticks(np.arange(len(input_data)))
    ax1.set_xticklabels((input_data[feature]).astype('str'))
    plt.xticks(rotation=45)
    ax1.set_xlabel('Bins of ' + feature)
    ax1.set_ylabel('Average of ' + target_col)
    comment = "Trend changed " + str(trend_changes) + " times"
    if trend_correlation == 0:
        comment = comment + '\n' + 'Correlation with train trend: NA'
    elif trend_correlation != None:
        comment = comment + '\n' + 'Correlation with train trend: ' + str(int(trend_correlation * 100)) + '%'

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.3)
    ax1.text(0.05, 0.95, comment, fontsize=12, verticalalignment='top', bbox=props, transform=ax1.transAxes)
    plt.title('Average of ' + target_col + ' wrt ' + feature)

    ax2 = plt.subplot(1, 2, 2)
    ax2.bar(np.arange(len(input_data)), input_data['Samples_in_bin'], alpha=0.5)
    ax2.set_xticks(np.arange(len(input_data)))
    ax2.set_xticklabels((input_data[feature]).astype('str'))
    plt.xticks(rotation=45)
    ax2.set_xlabel('Bins of ' + feature)
    ax2.set_ylabel('Bin-wise sample size')
    plt.title('Samples in bins of ' + feature)
    plt.tight_layout()
    plt.show()


def get_trend_changes(grouped_data, feature, target_col, threshold=0.03):
    grouped_data = grouped_data.loc[grouped_data[feature] != 'Nulls', :].reset_index(drop=True)
    target_diffs = grouped_data[target_col + '_mean'].diff()
    target_diffs = target_diffs[~np.isnan(target_diffs)].reset_index(drop=True)
    max_diff = grouped_data[target_col + '_mean'].max() - grouped_data[target_col + '_mean'].min()
    target_diffs_mod = target_diffs.abs()
    low_change = target_diffs_mod < threshold * max_diff
    target_diffs_norm = target_diffs.divide(target_diffs_mod)
    target_diffs_norm[low_change] = 0
    target_diffs_norm = target_diffs_norm[target_diffs_norm != 0]
    target_diffs_lvl2 = target_diffs_norm.diff()
    changes = target_diffs_lvl2.abs() / 2
    tot_trend_changes = int(changes.sum()) if ~np.isnan(changes.sum()) else 0
    return (tot_trend_changes)


def get_trend_correlation(grouped, grouped_test, feature, target_col):
    grouped = grouped[grouped[feature] != 'Nulls'].reset_index(drop=True)
    grouped_test = grouped_test[grouped_test[feature] != 'Nulls'].reset_index(drop=True)

    if grouped_test.loc[0, feature] != grouped.loc[0, feature]:
        grouped_test[feature] = grouped_test[feature].cat.add_categories(grouped.loc[0, feature])
        grouped_test.loc[0, feature] = grouped.loc[0, feature]
    grouped_test_train = grouped.merge(grouped_test[[feature, target_col + '_mean']], on=feature, how='left',
                                       suffixes=('', '_test'))
    trend_correlation = np.corrcoef(grouped_test_train[target_col + '_mean'],
                                    grouped_test_train[target_col + '_mean_test'])[0, 1]

    if np.isnan(trend_correlation):
        trend_correlation = 0
        print("Only one bin created and hence, correlation can't be calculated")
    return (trend_correlation)


def univariate_plotter(feature, data, target_col, bins=10, data_test=0):
    print('Plots for ' + feature)
    cuts, grouped = get_grouped_data(input_data=data, feature=feature, target_col=target_col, bins=bins)

    if type(data_test) == pd.core.frame.DataFrame:
        grouped_test = get_grouped_data(input_data=data_test.reset_index(drop=True), feature=feature,
                                        target_col=target_col, bins=bins, cuts=cuts)
        trend_corr = get_trend_correlation(grouped, grouped_test, feature, target_col)
        print('Train data plots')
        draw_plots(input_data=grouped, feature=feature, target_col=target_col)
        print('Test data plots')
        draw_plots(input_data=grouped_test, feature=feature, target_col=target_col, trend_correlation=trend_corr)
    else:
        draw_plots(input_data=grouped, feature=feature, target_col=target_col)
    print('--------------------------------------------------------------------------')
    print('\n')
    return (grouped, grouped_test)