import { Button, Flex, Select, Space, Typography } from 'antd';

import {
  ADMIN_PAGE_SIZE_OPTIONS,
  formatPageSummary,
  hasNextPage,
  hasPreviousPage,
  replacePaginationPageSize,
  shiftOffsetPagination,
  type OffsetPaginationFilters,
  type PaginatedResponse,
} from '../../features/auth/auth-client.js';

type OffsetPaginationControlsProps = {
  filters: OffsetPaginationFilters;
  response?: PaginatedResponse<unknown>;
  loading?: boolean;
  onChange: (nextFilters: OffsetPaginationFilters) => void;
  summarySuffix?: string;
};

export function OffsetPaginationControls({
  filters,
  response,
  loading = false,
  onChange,
  summarySuffix,
}: OffsetPaginationControlsProps): JSX.Element {
  const summary = response ? formatPageSummary(response) : `Page size ${filters.limit}`;
  const summaryText = summarySuffix ? `${summary} · ${summarySuffix}` : summary;

  return (
    <Flex align="center" justify="space-between" gap={12} wrap="wrap" style={{ marginBottom: 12 }}>
      <Typography.Text type="secondary">{summaryText}</Typography.Text>
      <Space wrap>
        <span style={{ color: 'rgba(0, 0, 0, 0.45)' }}>Page size</span>
        <Select
          value={filters.limit}
          style={{ width: 108 }}
          options={ADMIN_PAGE_SIZE_OPTIONS.map((value) => ({
            value,
            label: String(value),
          }))}
          disabled={loading}
          onChange={(value) => onChange(replacePaginationPageSize(filters, value))}
        />
        <Button disabled={!hasPreviousPage(filters) || loading} onClick={() => onChange(shiftOffsetPagination(filters, 'prev'))}>
          Previous page
        </Button>
        <Button disabled={!hasNextPage(response, filters) || loading} onClick={() => onChange(shiftOffsetPagination(filters, 'next'))}>
          Next page
        </Button>
      </Space>
    </Flex>
  );
}
