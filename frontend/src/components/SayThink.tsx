type Props = { said: string; thought: string };

export default function SayThink({ said, thought }: Props) {
  return (
    <div className="say-think">
      <div>
        <h3>Cosa dicono</h3>
        <p>{said}</p>
      </div>
      <div className="think">
        <h3>Cosa pensano</h3>
        <p>{thought}</p>
      </div>
    </div>
  );
}
