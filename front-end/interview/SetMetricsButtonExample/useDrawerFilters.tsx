import React, { useMemo, useState } from 'react';

import { SetMetricsButton } from '_shared/modules/nomination/components/SetMetricsButton';
import { ColumnGroup, SectionColumnGroup } from '_shared/modules/nomination/components/SetMetricsButton/types';
import { ListItemFilterKeys } from '_shared/modules/nomination/constants/enum';
import { getCategoryListTask } from '_shared/services/recruiting';
import { useMemoizedFn, useRequest } from 'ahooks';
import { compact, isNil } from 'lodash-es';
import {
  type FieldCellProps,
  reviewDrawerFilterFields,
} from 'src/_pagesCore/reviewPage/definitions/reviewDrawerFilterFields';

import { type DrawerFilterButtonItemProps, type FieldViewCellProps, FieldsGrid } from '@shopee/isfe-common-pattern';

export const useDrawerFilters = (): DrawerFilterButtonItemProps => {
  const { data: categories, loading: categoryLoading } = useRequest(getCategoryListTask);
  const sections: SectionColumnGroup[] = useMemo(
    () => [
      {
        title: 'Basic Info',
        fields: [
          reviewDrawerFilterFields[ListItemFilterKeys.ModelIds](),
          reviewDrawerFilterFields[ListItemFilterKeys.ItemIds](),
          reviewDrawerFilterFields[ListItemFilterKeys.NominationStatus](),
        ],
      },
      {
        title: 'By Shop',
        fields: compact([
          !categoryLoading &&
            reviewDrawerFilterFields[ListItemFilterKeys.GlobalCategory]({
              options: categories?.listBE ?? [],
            }),
          reviewDrawerFilterFields[ListItemFilterKeys.ShopIds](),
          reviewDrawerFilterFields[ListItemFilterKeys.ShopTier](),
          reviewDrawerFilterFields[ListItemFilterKeys.ShopPenalty](),
          reviewDrawerFilterFields[ListItemFilterKeys.CrossBorder](),
          reviewDrawerFilterFields[ListItemFilterKeys.ManagedSeller](),
          reviewDrawerFilterFields[ListItemFilterKeys.OnVacation](),
          reviewDrawerFilterFields[ListItemFilterKeys.OfficialSeller](),
          reviewDrawerFilterFields[ListItemFilterKeys.StarredSeller](),
          reviewDrawerFilterFields[ListItemFilterKeys.AvgPrepTime](),
          reviewDrawerFilterFields[ListItemFilterKeys.ShopRating](),
          reviewDrawerFilterFields[ListItemFilterKeys.NumberOfShopRatings](),
        ]),
      },
      {
        title: 'By Product',
        fields: [
          reviewDrawerFilterFields[ListItemFilterKeys.ItemNames](),
          reviewDrawerFilterFields[ListItemFilterKeys.SoldLast30days](),
          reviewDrawerFilterFields[ListItemFilterKeys.SoldAllTime](),
          reviewDrawerFilterFields[ListItemFilterKeys.NumberOfLikes](),
          reviewDrawerFilterFields[ListItemFilterKeys.ConversionRate](),
          reviewDrawerFilterFields[ListItemFilterKeys.Condition](),
          reviewDrawerFilterFields[ListItemFilterKeys.AverageDailyOrderL7D](),
          reviewDrawerFilterFields[ListItemFilterKeys.AverageDailyOrderL30D](),
          reviewDrawerFilterFields[ListItemFilterKeys.DaysToShip](),
          reviewDrawerFilterFields[ListItemFilterKeys.PreOrder](),
          reviewDrawerFilterFields[ListItemFilterKeys.CurrentStock](),
          reviewDrawerFilterFields[ListItemFilterKeys.PromoStock](),
          reviewDrawerFilterFields[ListItemFilterKeys.FreeShippingService](),
          reviewDrawerFilterFields[ListItemFilterKeys.ServiceByShopee](),
          reviewDrawerFilterFields[ListItemFilterKeys.CoinsCashBack](),
          reviewDrawerFilterFields[ListItemFilterKeys.NumberOfProductRating](),
        ],
      },
      {
        title: 'By Nomination',
        fields: [
          reviewDrawerFilterFields[ListItemFilterKeys.OverlapPriceComparison](),
          reviewDrawerFilterFields[ListItemFilterKeys.NominationSource](),
          reviewDrawerFilterFields[ListItemFilterKeys.OnlyShowRiskItems](),
          reviewDrawerFilterFields[ListItemFilterKeys.OnlyShowSoftWarning](),
          reviewDrawerFilterFields[ListItemFilterKeys.AdjustPromoStock](),
          reviewDrawerFilterFields[ListItemFilterKeys.OverlappedPromoType](),
          reviewDrawerFilterFields[ListItemFilterKeys.SecondAssignReviewers](),
          reviewDrawerFilterFields[ListItemFilterKeys.Creators](),
          reviewDrawerFilterFields[ListItemFilterKeys.CreateTime](),
          reviewDrawerFilterFields[ListItemFilterKeys.Operators](),
          reviewDrawerFilterFields[ListItemFilterKeys.LastUpdateAction](),
          reviewDrawerFilterFields[ListItemFilterKeys.LastUpdateTime](),
          reviewDrawerFilterFields[ListItemFilterKeys.NominationRemark](),
        ],
      },
      {
        title: 'By Price',
        fields: [
          reviewDrawerFilterFields[ListItemFilterKeys.Discount](),
          reviewDrawerFilterFields[ListItemFilterKeys.PriceCheckHardResult](),
          reviewDrawerFilterFields[ListItemFilterKeys.PriceCheckSoftResult](),
        ],
      },
    ],
    [categories?.listBE, categoryLoading]
  );

  const [finalColumnGroups, setFinalColumnGroups] = useState<ColumnGroup[]>([]);

  const onFinalColumnGroupsChange = useMemoizedFn((_finalColumnGroups) => {
    setFinalColumnGroups(_finalColumnGroups);
  });

  const filteredSections: SectionColumnGroup[] = useMemo(() => {
    if (!finalColumnGroups.length) return sections;
    return sections.map((section, index) => {
      const columnGroup = finalColumnGroups[index];
      return {
        title: section.title,
        fields: section.fields.filter((field) => {
          const column = columnGroup.fields.find((column) => column.dataIndex === field.name);
          return column?.selected ?? true;
        }),
      };
    });
  }, [finalColumnGroups, sections]);

  return useMemo(() => {
    const drawerFiltersButtonProps: DrawerFilterButtonItemProps = {
      buttonType: 'drawer-filter-button',
      drawerProps: {
        closable: true,
        title: (
          <>
            Filter{' '}
            <SetMetricsButton
              persistentKey={'FS-Review'}
              sections={sections}
              onFinalColumnGroupsChange={onFinalColumnGroupsChange}
            />
          </>
        ),
      },
      sections: filteredSections,
    };

    return {
      ...drawerFiltersButtonProps,
      renderFilterInfo: (filterValues: { [x: string]: unknown }): JSX.Element => {
        return (
          <FieldsGrid
            direction="column"
            columnCount={1}
            fields={
              filteredSections
                .flatMap((section) => section.fields)
                .filter((field: FieldCellProps) => !isNil(filterValues[field.name]))
                .map((field: FieldCellProps) => ({
                  ...field,
                  value: field.renderFilterInfo
                    ? field.renderFilterInfo(filterValues[field.name])
                    : filterValues[field.name],
                })) as FieldViewCellProps[]
            }
          />
        );
      },
    };
  }, [sections, onFinalColumnGroupsChange, filteredSections]);
};
