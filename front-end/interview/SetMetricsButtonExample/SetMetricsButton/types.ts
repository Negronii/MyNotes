import { FormFieldCellProps } from '@shopee/isfe-common-pattern';

export interface MetricsField {
  dataIndex: string;
  title: React.ReactNode;
  selected: boolean;
  fixed?: boolean;
}

export type ColumnGroup = {
  groupName: string;
  fields: MetricsField[];
};

export type SectionColumnGroup = {
  title: string;
  fields: FormFieldCellProps[];
};

export type UseSetMetricsProps = {
  persistentKey: string;
  sections: SectionColumnGroup[];
};

export type MetricsSetterReturnType = {
  draftColumnGroups: ColumnGroup[];
  finalColumnGroups: ColumnGroup[];
  init: () => void;
  update: () => void;
  onSelectAll: () => void;
  onUnselectAll: () => void;
  onSelectField: (groupName: string, fieldDataIndex: string, selected: boolean) => void;
};
