// Metro resolves image imports to a numeric asset reference.
declare module "*.png" {
  const asset: number;
  export default asset;
}
