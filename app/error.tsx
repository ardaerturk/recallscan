"use client";

import { PackageSearch } from "lucide-react";

export default function ErrorBoundary({
  unstable_retry,
}: {
  error: Error & { digest?: string };
  unstable_retry: () => void;
}) {
  return (
    <main className="flex min-h-svh items-center justify-center bg-[#090909] px-6 text-zinc-100">
      <section className="w-full max-w-md rounded-lg border border-white/10 bg-[#101010] p-6">
        <div className="flex size-9 items-center justify-center rounded-md bg-white text-black">
          <PackageSearch className="size-4" />
        </div>
        <h1 className="mt-5 text-2xl font-semibold tracking-normal text-white">Something went wrong.</h1>
        <p className="mt-3 text-sm leading-6 text-zinc-500">
          Refresh the dashboard and try again. If the issue continues, check the API health endpoint.
        </p>
        <button
          type="button"
          onClick={() => unstable_retry()}
          className="mt-6 inline-flex h-10 items-center rounded-md bg-white px-4 text-sm font-medium text-black transition hover:bg-zinc-200"
        >
          Retry
        </button>
      </section>
    </main>
  );
}
