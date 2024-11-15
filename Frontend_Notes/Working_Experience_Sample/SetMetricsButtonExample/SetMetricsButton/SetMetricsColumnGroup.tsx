import React, { memo } from 'react';

import { useMemoizedFn } from 'ahooks';
import { Checkbox } from 'antd';

import { MetricsField } from './types';

import styles from './SetMetricsButton.module.scss';

type SetMetricsColumnGroupProps = {
  groupName: string;
  fields: MetricsField[];
  onColumnClick: (groupName: string, fieldDataIndex: string, selected: boolean) => void;
  columnQuantity: number;
};

export const SetMetricsColumnGroup = memo((props: SetMetricsColumnGroupProps): JSX.Element => {
  const { groupName, fields, onColumnClick, columnQuantity } = props;

  const columnWidth = React.useMemo(() => (columnQuantity < 2 ? 250 : 150), [columnQuantity]);

  const itemInfos = React.useMemo(() => {
    if (!fields?.length) return [];

    const infos = [];
    const length = fields.length;
    const chunkSize = 8;

    for (let start = 0; start < length; start += chunkSize) {
      const end = Math.min(start + chunkSize, length);
      infos.push({
        items: fields.slice(start, end),
        start,
        end,
      });
    }

    return infos;
  }, [fields]);

  return (
    <div className={styles.columnCategory}>
      {groupName && <h2>{groupName}</h2>}
      <div className={styles.categoryColumn}>
        {itemInfos.map((itemInfo, index) => (
          <SetMetricsSingleColumn
            key={index}
            groupName={groupName}
            items={itemInfo.items}
            columnWidth={columnWidth}
            columnQuantity={columnQuantity}
            onItemClick={onColumnClick}
          />
        ))}
      </div>
    </div>
  );
});

SetMetricsColumnGroup.displayName = 'SetMetricsColumnGroup';

interface SetMetricsSingleColumnProps {
  groupName: string;
  items: MetricsField[];
  columnQuantity: number;
  columnWidth: number;
  onItemClick: SetMetricsColumnGroupProps['onColumnClick'];
}

export const SetMetricsSingleColumn = memo((props: SetMetricsSingleColumnProps): JSX.Element => {
  const { groupName, items, onItemClick, columnQuantity, columnWidth, ...restProps } = props;

  return (
    <div
      {...restProps}
      className={columnQuantity < 2 ? styles.itemSingleColumn : styles.itemMultipleColumns}
      style={{ width: columnWidth }}
    >
      {items.map((item, idx) => (
        <MetricsCheckboxItem
          key={item.dataIndex}
          groupName={groupName}
          index={idx}
          onColumnClick={onItemClick}
          {...item}
        />
      ))}
    </div>
  );
});

SetMetricsSingleColumn.displayName = 'SetMetricsSingleColumn';

interface MetricsCheckboxItemProps extends MetricsField {
  index: number;
  groupName: string;
  onColumnClick: SetMetricsColumnGroupProps['onColumnClick'];
}

export const MetricsCheckboxItem = memo(
  (props: MetricsCheckboxItemProps): JSX.Element => {
    const { index: idx, groupName, onColumnClick, ...item } = props;
    const handleOnClick = useMemoizedFn((ev) => onColumnClick(groupName, item.dataIndex, ev.target.checked));

    return (
      <div
        className={styles.singleItemWrapper}
        style={{ marginBottom: idx === 7 ? 0 : '16px' }}
        key={item.dataIndex + idx}
      >
        <Checkbox
          style={{
            opacity: item.fixed ? 0.5 : 1,
            pointerEvents: item.fixed ? 'none' : 'auto',
            paddingRight: 8,
          }}
          defaultChecked={item.selected}
          checked={item.selected}
          onClick={handleOnClick}
        />
        <span style={{ margin: 0 }}>{item.title}</span>
      </div>
    );
  },
  (prevProps, nextProps) => prevProps.selected === nextProps.selected
);

MetricsCheckboxItem.displayName = 'MetricsColumnItem';
