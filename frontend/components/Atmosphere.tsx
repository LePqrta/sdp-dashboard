export function Atmosphere() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="atmosphere-blob atmosphere-blob-mint" />
      <div className="atmosphere-blob atmosphere-blob-orchid" />
      <div className="atmosphere-blob atmosphere-blob-apricot" />
      <div className="absolute inset-0 dot-field opacity-70" />
    </div>
  );
}
