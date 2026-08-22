// A react-query cache key is a cache key, not a telemetry sink.
export const useLenders = (walletAddress: string) =>
  useQuery({
    queryKey: ["lenders", walletAddress],
    queryFn: () => fetchLenders(walletAddress),
  })
