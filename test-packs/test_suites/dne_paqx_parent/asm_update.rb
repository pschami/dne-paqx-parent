#!/usr/bin/env ruby

#
# ASM updates
# Tool to update/patch ASM
#

require "getoptlong"
require "json"
require "fileutils"
require "tempfile"

# Define file locations
YUM_LOG = "/var/log/yum.log"
ASM_YUM = "/opt/Dell/ASM/logs/asmyum.log".freeze
ASM_VERSION_JSON = "/opt/Dell/ASM/logs/asmUpdate.json".freeze
ASM_PATCH_LOG = "/opt/Dell/ASM/logs/asmPatch.log".freeze

# Generates/maintains copy of yum.log
#
# @note Generates /opt/Dell/ASM/logs/asmyum.log
# @note a subset of /var/log/yum.log
def gen_yumlog
  File.open(YUM_LOG).readlines.each do |line|
    File.write(ASM_YUM, line, mode: "a") if line.include? "Dell-ASM-AsmManager"
  end
  tmpfile = Tempfile.new("yumlog", "/opt/Dell/ASM/logs")
  File.open(tmpfile, "w") { |file| file.puts File.readlines(ASM_YUM).uniq }
  FileUtils.mv(tmpfile, ASM_YUM)
end

# Get the AsmManager package installation date
#
# @param [String] name of AsmManager pkg
# @return [String] the resulting package install date
def get_date(pkgname)
  IO.readlines("|/usr/bin/yum history list #{pkgname}").last(2)[0].split("|")[2].strip
end

# Writes ASM installed/updated version history
#
# @note Generates /opt/Dell/ASM/logs/asmUpdate.json
def gen_history
  gen_yumlog
  yuminfo = []
  File.open(ASM_YUM, "r").each_line do |line|
    month, day, time, type, name = line.split
    next unless name.include?"Dell-ASM-AsmManager"
    version = name.split("-")[3]
    buildnum = name.split("-")[4].split(".")[0]
    type = type.split(":")[0]
    date = get_date(name)
    pkginfo = {asmversion: version, build: buildnum, date: date, operation: type}
    yuminfo << pkginfo
  end
  File.write(ASM_VERSION_JSON, JSON.pretty_generate(yuminfo), mode: "w")
end

# Yum update Appliance and generate asmversion file
def update_appliance
  cmd = "/usr/bin/yum -y --disablerepo=* --enablerepo=asmcustom update"
  system(cmd)
  gen_history
end

# Parse asmUpdate.json file and display to screen
def show_asm_version
  gen_history
  JSON.parse(File.read(ASM_VERSION_JSON)).each do |elem|
    printf "\t%s\t\t%s\t%s\t%s\n", elem["asmversion"], elem["build"], elem["date"], elem["operation"]
  end
  if File.file?(ASM_PATCH_LOG)
    puts "\nWith the current updated patches"
    puts File.read(ASM_PATCH_LOG)
  end
end

# Main
#
opts = GetoptLong.new(
  ["--help", "-h", GetoptLong::NO_ARGUMENT],
  ["--update", "-u", GetoptLong::NO_ARGUMENT],
  ["--patch", "-p", GetoptLong::REQUIRED_ARGUMENT],
  ["--display", "-d", GetoptLong::NO_ARGUMENT]
)

opts_found = false
opts.each do |opt|
  opts_found = true
  case opt
  when "--help"
    puts "Usage: %s -u -h -d", $0
    printf "Where\t-u|--update\t: Will update the ASM appliance to the latest available level\n"
    printf "\t-d|--display\t: Shows the current ASM versions\n"
    puts " \t-h|--help\t: Shows this usage"
    exit 0
  when "--update"
    printf "Updating Appliance to latest level\n"
    update_appliance
  when "--display"
    printf "\tVersion\t\tBuild\t\tDate\t\tOperation\n"
    printf "%s\n", "-" * 69
    show_asm_version
  end
end

printf "Please run \"%s --help\" for list of options\n", $0 unless opts_found
