import type { CSSProperties } from 'react'
import { Select } from 'antd'
import { useProductsV2 } from '@/hooks'
import type { ProductResponse } from '@/types/material'

interface ProductSelectProps {
  value?: number
  onChange?: (value: number | undefined) => void
  placeholder?: string
  allowClear?: boolean
  style?: CSSProperties
}

export default function ProductSelect({ value, onChange, placeholder, allowClear, style }: ProductSelectProps) {
  const { data: products = [] } = useProductsV2()
  const options = products.map((p: ProductResponse) => ({ label: p.name, value: p.id }))

  return (
    <Select
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      allowClear={allowClear}
      style={style}
      options={options}
    />
  )
}
