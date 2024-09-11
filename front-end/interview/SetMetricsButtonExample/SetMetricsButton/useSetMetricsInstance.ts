import { useCallback, useEffect, useState } from 'react';

import { useMemoizedFn } from 'ahooks';
import { isBoolean } from 'lodash';

import { usePersistentState } from '@shopee/isfe-common-pattern';

import { ColumnGroup, MetricsSetterReturnType, UseSetMetricsProps } from './types';

export const useSetMetrics = (props: UseSetMetricsProps): MetricsSetterReturnType => {
  const { persistentKey, sections: sectionsFromProps } = props;

  const [draftColumnGroups, setDraftColumnGroups] = useState<ColumnGroup[]>([]);
  const [finalColumnGroups, setFinalColumnGroups] = useState<ColumnGroup[]>([]);
  const [hiddenFields, setHiddenFields] = usePersistentState<string[]>('hiddenColumns-' + persistentKey);

  const init = useCallback((): void => {
    const _hiddenColumns = hiddenFields || [];

    const _columnGroups: ColumnGroup[] = sectionsFromProps.map((section) => {
      return {
        groupName: section.title,
        fields: section.fields.map((field) => {
          const selected =
            'selected' in field && isBoolean(field.selected) ? field.selected : !_hiddenColumns.includes(field.name);
          return {
            dataIndex: field.name,
            title: field.label,
            selected: selected,
          };
        }),
      };
    });

    setDraftColumnGroups(_columnGroups);
    setFinalColumnGroups(_columnGroups);
  }, [hiddenFields, sectionsFromProps]);

  useEffect(() => {
    init();
  }, [init]);

  const update = useMemoizedFn(() => {
    setHiddenFields(
      draftColumnGroups.flatMap((_columnGroup) =>
        _columnGroup.fields.filter((field) => !field.selected).map((field) => field.dataIndex)
      )
    );

    setFinalColumnGroups(draftColumnGroups);
  });

  const onSelectAll = useMemoizedFn(() => {
    setDraftColumnGroups(
      draftColumnGroups.map((_columnGroup) => ({
        groupName: _columnGroup.groupName,
        fields: _columnGroup.fields.map((field) => {
          if (!field.selected) {
            return {
              ...field,
              selected: true,
            };
          }
          return field;
        }),
      }))
    );
  });

  const onUnselectAll = useMemoizedFn(() => {
    setDraftColumnGroups(
      draftColumnGroups.map((_columnGroup) => ({
        groupName: _columnGroup.groupName,
        fields: _columnGroup.fields.map((field) => {
          if (field.selected) {
            return {
              ...field,
              selected: false,
            };
          }
          return field;
        }),
      }))
    );
  });

  const onSelectField = useMemoizedFn((groupName: string, fieldDataIndex: string, selected: boolean) => {
    setDraftColumnGroups(
      draftColumnGroups.map((_columnGroup) => {
        if (_columnGroup.groupName === groupName) {
          return {
            groupName: _columnGroup.groupName,
            fields: _columnGroup.fields.map((field) => {
              if (field.dataIndex === fieldDataIndex) {
                return {
                  ...field,
                  selected: selected,
                };
              }
              return field;
            }),
          };
        }
        return _columnGroup;
      })
    );
  });

  const instance = {
    draftColumnGroups,
    finalColumnGroups,
    // api
    init,
    update,
    // events
    onSelectAll,
    onUnselectAll,
    onSelectField,
  };

  return instance;
};
