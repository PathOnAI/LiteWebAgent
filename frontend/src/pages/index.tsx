import Playground from "./playground"

export default function Page() {
  return <Playground initialSteps_={[]} processId="x" onSessionEnd={() => console.log('done')}  />
}