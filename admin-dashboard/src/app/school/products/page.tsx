"use client";

import { Badge, Button, Checkbox, Group, Modal, Select, Stack, Tabs, TextInput } from "@mantine/core";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { ChoiceFilter } from "@/components/filters";
import { ConfirmAction, DataTable, ErrorAlert, Money, PageHeader, StatusBadge } from "@/components/ui";
import { api, type Paginated } from "@/lib/api";
import { useApi, usePaginated } from "@/lib/hooks";
import { isValidAmount } from "@/lib/money";

type Category = { id: number; name: string; is_unhealthy: boolean; active: boolean };
type Product = { id: number; name: string; category: number; category_name: string; price: string; active: boolean; merchant: number | null };
type Merchant = { id: number; name: string; my_school_approval: string | null };

export default function ProductsPage() {
  const t = useTranslations("products");
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} />
      <Tabs defaultValue="products">
        <Tabs.List>
          <Tabs.Tab value="products">{t("products")}</Tabs.Tab>
          <Tabs.Tab value="categories">{t("categories")}</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="products" pt="md">
          <Products />
        </Tabs.Panel>
        <Tabs.Panel value="categories" pt="md">
          <Categories />
        </Tabs.Panel>
      </Tabs>
    </>
  );
}

function Categories() {
  const t = useTranslations("products");
  const list = usePaginated<Category>("/product-categories/");
  return (
    <>
      <Group justify="flex-end" mb="sm">
        <CategoryForm onDone={list.reload} />
      </Group>
      <DataTable<Category>
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        columns={[
          { key: "name", header: t("name") },
          { key: "is_unhealthy", header: t("unhealthy"), render: (c) => (c.is_unhealthy ? <Badge color="red">{t("unhealthy")}</Badge> : "—") },
          { key: "active", header: t("active"), render: (c) => <StatusBadge status={c.active ? "active" : "closed"} /> },
          {
            key: "actions",
            header: "",
            render: (c) => (
              <Group gap="xs">
                <CategoryForm category={c} onDone={list.reload} />
                <ConfirmAction label={t("delete")} color="red" title={t("deleteCategory")} description={t("deleteCategoryHelp", { name: c.name })} onConfirm={() => api.del(`/product-categories/${c.id}/`)} onDone={list.reload} />
              </Group>
            ),
          },
        ]}
      />
    </>
  );
}

function CategoryForm({ category, onDone }: { category?: Category; onDone: () => void }) {
  const t = useTranslations("products");
  const [open, setOpen] = useState(false);
  const [v, setV] = useState({ name: category?.name ?? "", is_unhealthy: category?.is_unhealthy ?? false, active: category?.active ?? true });
  const [error, setError] = useState<unknown>(null);
  const save = async () => {
    setError(null);
    try {
      if (category) await api.patch(`/product-categories/${category.id}/`, v);
      else await api.post("/product-categories/", v);
      setOpen(false);
      onDone();
    } catch (e) {
      setError(e);
    }
  };
  return (
    <>
      <Button size="xs" variant={category ? "light" : "filled"} onClick={() => setOpen(true)}>
        {category ? t("edit") : t("newCategory")}
      </Button>
      <Modal opened={open} onClose={() => setOpen(false)} title={category ? t("edit") : t("newCategory")} centered>
        <Stack>
          <TextInput label={t("name")} value={v.name} onChange={(e) => setV({ ...v, name: e.currentTarget.value })} required />
          <Checkbox label={t("unhealthyLabel")} checked={v.is_unhealthy} onChange={(e) => setV({ ...v, is_unhealthy: e.currentTarget.checked })} />
          <Checkbox label={t("active")} checked={v.active} onChange={(e) => setV({ ...v, active: e.currentTarget.checked })} />
          <ErrorAlert error={error} />
          <Group justify="flex-end">
            <Button onClick={save} disabled={!v.name}>
              {t("save")}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}

function Products() {
  const t = useTranslations("products");
  const [category, setCategory] = useState("");
  const [merchant, setMerchant] = useState("");
  const cats = useApi<Paginated<Category>>("/product-categories/", { page_size: 100 });
  const merchants = useApi<Paginated<Merchant>>("/merchants/", { page_size: 100 });
  const approved = (merchants.data?.results ?? []).filter((m) => m.my_school_approval === "approved");
  const list = usePaginated<Product>("/products/", { category, merchant });
  const merchantName = (id: number | null) => (id ? (approved.find((m) => m.id === id)?.name ?? `#${id}`) : t("canteen"));
  return (
    <>
      <Group justify="space-between" mb="sm" align="flex-end">
        <Group>
          <ChoiceFilter label={t("category")} value={category} onChange={setCategory} options={(cats.data?.results ?? []).map((c) => ({ value: String(c.id), label: c.name }))} />
          <ChoiceFilter label={t("merchant")} value={merchant} onChange={setMerchant} options={approved.map((m) => ({ value: String(m.id), label: m.name }))} />
        </Group>
        <ProductForm categories={cats.data?.results ?? []} merchants={approved} onDone={list.reload} />
      </Group>
      <DataTable<Product>
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        columns={[
          { key: "name", header: t("name") },
          { key: "category_name", header: t("category") },
          { key: "price", header: t("price"), render: (p) => <Money value={p.price} /> },
          { key: "merchant", header: t("soldBy"), render: (p) => merchantName(p.merchant) },
          { key: "active", header: t("active"), render: (p) => <StatusBadge status={p.active ? "active" : "closed"} /> },
          {
            key: "actions",
            header: "",
            render: (p) => (
              <Group gap="xs">
                <ProductForm product={p} categories={cats.data?.results ?? []} merchants={approved} onDone={list.reload} />
                <ConfirmAction label={t("delete")} color="red" title={t("deleteProduct")} description={t("deleteProductHelp", { name: p.name })} onConfirm={() => api.del(`/products/${p.id}/`)} onDone={list.reload} />
              </Group>
            ),
          },
        ]}
      />
    </>
  );
}

function ProductForm({ product, categories, merchants, onDone }: { product?: Product; categories: Category[]; merchants: Merchant[]; onDone: () => void }) {
  const t = useTranslations("products");
  const [open, setOpen] = useState(false);
  const [v, setV] = useState({
    name: product?.name ?? "",
    category: product ? String(product.category) : "",
    price: product?.price ?? "",
    active: product?.active ?? true,
    merchant: product?.merchant ? String(product.merchant) : "",
  });
  const [error, setError] = useState<unknown>(null);
  const save = async () => {
    setError(null);
    const body = { name: v.name, category: Number(v.category), price: v.price, active: v.active, merchant: v.merchant ? Number(v.merchant) : null };
    try {
      if (product) await api.patch(`/products/${product.id}/`, body);
      else await api.post("/products/", body);
      setOpen(false);
      onDone();
    } catch (e) {
      setError(e);
    }
  };
  return (
    <>
      <Button size="xs" variant={product ? "light" : "filled"} onClick={() => setOpen(true)}>
        {product ? t("edit") : t("newProduct")}
      </Button>
      <Modal opened={open} onClose={() => setOpen(false)} title={product ? t("edit") : t("newProduct")} centered>
        <Stack>
          <TextInput label={t("name")} value={v.name} onChange={(e) => setV({ ...v, name: e.currentTarget.value })} required />
          <Select label={t("category")} value={v.category} onChange={(x) => setV({ ...v, category: x ?? "" })} data={categories.map((c) => ({ value: String(c.id), label: c.name }))} required />
          <TextInput label={t("priceUgx")} value={v.price} onChange={(e) => setV({ ...v, price: e.currentTarget.value })} error={v.price && !isValidAmount(v.price) ? t("priceInvalid") : undefined} required />
          <Select
            label={t("soldBy")}
            value={v.merchant}
            onChange={(x) => setV({ ...v, merchant: x ?? "" })}
            data={[{ value: "", label: t("canteen") }, ...merchants.map((m) => ({ value: String(m.id), label: m.name }))]}
            allowDeselect={false}
          />
          <Checkbox label={t("active")} checked={v.active} onChange={(e) => setV({ ...v, active: e.currentTarget.checked })} />
          <ErrorAlert error={error} />
          <Group justify="flex-end">
            <Button onClick={save} disabled={!v.name || !v.category || !isValidAmount(v.price)}>
              {t("save")}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}
