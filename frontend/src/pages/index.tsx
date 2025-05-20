import type { GetServerSidePropsContext } from "next";
import { useRouter } from "next/router";
import { createClient } from "@/utils/supabase/server-props";
import { BrainCircuit } from "lucide-react";

interface PageProps {
  user?: any;
}

export default function Page({ user }: PageProps) {
  const router = useRouter();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-gray-50 via-gray-50 to-blue-50">
      {/* Enlarged Logo and Title Section */}
      <div className="flex items-center space-x-6 mb-12">
        <div className="bg-gradient-to-br from-blue-600 to-indigo-600 text-white p-6 rounded-2xl shadow-xl flex items-center justify-center">
          <BrainCircuit className="w-16 h-16" />
        </div>
        <div>
          <span className="font-semibold text-gray-800 text-4xl block mb-2">Web Agent Demo</span>
          <p className="text-2xl text-gray-500">Interactive Browser Assistant</p>
        </div>
      </div>
      {user ? (
        <button
          onClick={() => router.push("/playground")}
          className="px-8 py-3 rounded-lg bg-blue-600 text-white font-semibold text-xl hover:bg-blue-700 transition"
        >
          Go to Playground
        </button>
      ) : (
        <div className="flex flex-col items-center">
          <h1 className="text-2xl font-bold mb-4">Please log in to view this page.</h1>
          <button
            onClick={() => router.push("/login")}
            className="px-6 py-2 rounded bg-blue-600 text-white font-semibold hover:bg-blue-700 transition"
          >
            Go to Login
          </button>
        </div>
      )}
    </div>
  );
}

export async function getServerSideProps(context: GetServerSidePropsContext) {
  const supabase = createClient(context);
  const { data } = await supabase.auth.getUser();

  return {
    props: {
      user: data?.user || null,
    },
  };
}