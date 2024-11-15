import React, { memo, useEffect, useMemo, useState } from 'react';

import { DownOutlined } from '@ant-design/icons';
import { useBoolean, useMemoizedFn } from 'ahooks';

import { Button, Modal } from '@shopee/isfe-common-pattern';

import { SetMetricsColumnGroup } from './SetMetricsColumnGroup';
import { ColumnGroup, UseSetMetricsProps } from './types';
import { useSetMetrics } from './useSetMetricsInstance';

import { columSetter, flexContainer, linkButton } from './SetMetricsButton.module.scss';
import styles from './SetMetricsButton.module.scss';

export type SetMetricsButtonProps = UseSetMetricsProps & {
  onFinalColumnGroupsChange: (_finalColumnGroups: ColumnGroup[]) => void;
};

export const SetMetricsButton = memo((props: SetMetricsButtonProps): JSX.Element => {
  const { persistentKey, sections, onFinalColumnGroupsChange } = props;

  const { draftColumnGroups, finalColumnGroups, init, update, onSelectAll, onUnselectAll, onSelectField } =
    useSetMetrics({
      persistentKey,
      sections,
    });

  const [visible, { setTrue, setFalse }] = useBoolean(false);
  const [columnTotalLength, setColumnTotalLength] = useState(0);
  const [closeAction, setCloseAction] = useState<'ok' | 'cancel' | null>(null);

  useEffect(() => {
    let columnLength = 0;
    finalColumnGroups.forEach(({ fields }) => {
      columnLength += Math.ceil(fields.length / 8);
    });
    setColumnTotalLength(columnLength);
  }, [finalColumnGroups]);

  const handleOnOK = useMemoizedFn(() => {
    setCloseAction('ok');
    setFalse();
  });

  const handleCancel = useMemoizedFn(() => {
    setCloseAction('cancel');
    setFalse();
  });

  useEffect(() => {
    onFinalColumnGroupsChange(finalColumnGroups);
  }, [finalColumnGroups, onFinalColumnGroupsChange]);

  // Improve user experience by setting the state after the modal is closed
  const afterClose = useMemoizedFn(() => {
    switch (closeAction) {
      case 'ok':
        update();
        break;
      case 'cancel':
        init();
        break;
    }
    // Reset the action
    setCloseAction(null);
  });

  const Footer = useMemo(
    () => (
      <div className={flexContainer}>
        <div>
          <button className={linkButton} onClick={onSelectAll}>
            Select All
          </button>
          /
          <button className={linkButton} onClick={onUnselectAll}>
            Unselect All
          </button>
        </div>
        <Button type="primary" onClick={handleOnOK}>
          OK
        </Button>
      </div>
    ),
    [onSelectAll, onUnselectAll, handleOnOK]
  );

  return (
    <>
      <Button onClick={setTrue} className={styles.setMetricsBtn}>
        Set Metrics <DownOutlined />
      </Button>
      <Modal
        visible={visible}
        onCancel={handleCancel}
        title="Set Metrics"
        width="max-content"
        closable={false}
        maskStyle={{ background: 'transparent' }}
        maskClosable
        afterClose={afterClose}
        footer={Footer}
      >
        <div className={columSetter}>
          {draftColumnGroups.map(({ groupName, fields }, idx) => (
            <SetMetricsColumnGroup
              key={groupName + idx}
              groupName={groupName}
              fields={fields}
              onColumnClick={onSelectField}
              columnQuantity={columnTotalLength}
            />
          ))}
        </div>
      </Modal>
    </>
  );
});

SetMetricsButton.displayName = 'SetMetricsButton';
