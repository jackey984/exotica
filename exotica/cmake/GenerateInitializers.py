#!/usr/bin/env python
import sys
import os

def eprint(msg):
    sys.stderr.write(msg+'\n')
    sys.exit(2)

def ConstructorArgumentList(Data):
    ret=""
    for d in Data:
        if d.has_key('Required'):
            ret+=" "+d['Type']+" "+d['Name']+"_"+DefaultArgumentValue(d)+","
    return ret[0:-1]

def ConstructorList(Data):
    ret=""
    for d in Data:
        if d.has_key('Required'):
            ret+=",\n        "+d['Name']+"(\""+d['Type']+"\", \""+d['Name']+"\", "+IsRequired(d)+", "+d['Name']+"_) "
    return ret

def DefaultValue(Data):
    if Data['Value']==None:
        return ""
    elif Data['Value']=='{}':
        return ""
    else:
        return ", "+Data['Value']

def DefaultArgumentValue(Data):
    if Data['Value']==None:
        return ""
    elif Data['Value']=='{}':
        return "={}"
    else:
        return " = "+Data['Value']

def IsRequired(Data):
    if Data['Required']:
        return "true"
    else:
        return "false"

def DefaultConstructorList(Data):
    ret=""
    for d in Data:
        if d.has_key('Required'):
            ret+=",\n        "+d['Name']+"(\""+d['Type']+"\", \""+d['Name']+"\", "+IsRequired(d)+DefaultValue(d)+") "
    return ret

def NeedsDefaultConstructor(Data):
    for d in Data:
        if d['Required']:
            return True
    return False

def Declaration(Data):
    if Data.has_key('Required'):
      return "    Property<"+Data['Type']+"> "+Data['Name']+";\n"
    else:
      return ""

def Copy(Data):
    if Data.has_key('Required'):
      return "        "+Data['Name']+" = other."+Data['Name']+";\n"
    else:
      return ""

def Register(Data):
    if Data.has_key('Required'):
      return "        properties_[\""+Data['Name']+"\"] = static_cast<PropertyElement*>(&"+Data['Name']+");\n" + "        propertiesOrdered_.push_back( static_cast<PropertyElement*>(&"+Data['Name']+") );\n"
    else:
      return ""

def Construct(Namespace, ClassName, Data,Include):
    CalssNameOrig=ClassName[0:-11]
    ret="""// This file was automatically generated. Do not edit this file!
#ifndef INITIALIZER_"""+Namespace+"_"+ClassName+"""_H
#define INITIALIZER_"""+Namespace+"_"+ClassName+"""_H

#include "exotica/Property.h"
"""
    for i in Include:
        ret+=i+"\n"
    ret+="""

namespace """ +Namespace+ """
{

class """+ClassName+" : public PropertyContainer"+"""
{
public:
    static std::string getContainerName() {return """+"\""+Namespace+"/"+CalssNameOrig+"\""+ """ ;}

    """
    if NeedsDefaultConstructor(Data):
        ret=ret+ClassName+"() : PropertyContainer(\""+Namespace+"/"+CalssNameOrig+"\")"+DefaultConstructorList(Data)+"""
    {
        RegisterParams();
    }

    """
    ret=ret+ClassName+"("+ConstructorArgumentList(Data)+") : PropertyContainer(\""+Namespace+"::"+ClassName+"\")"+ConstructorList(Data)+"""
    {
        RegisterParams();
    }

    """+ClassName+"""(const PropertyContainer& other)
    {
        RegisterParams();
        for(auto& param : properties_)
        {
            if(other.getProperties().find(param.first)!= other.getProperties().end())
            {
                // Copies over typeless PropertyElements using a virtual copyValue method
                *properties_[param.first] = *other.getProperties().at(param.first);
            }
            else
            {
                //problem
                throw_pretty("Combining incompatible initializers!");
            }
        }
    }

    void RegisterParams()
    {
"""
    for d in Data:
        ret+=Register(d)
    ret+="""    }

    void RegisterParams("""+ClassName+"""& other)
    {
"""
    for d in Data:
        ret+=Copy(d)
    ret+="""        RegisterParams();
    }

    void RegisterParams(const """+ClassName+"""& other)
    {
"""
    for d in Data:
        ret+=Copy(d)
    ret+="""        RegisterParams();
    }
"""
    for d in Data:
        ret+=Declaration(d)
    ret+="};\n}\n#endif"
    return ret

def ParseLine(line, ln, fn):
    last = line.find(";")
    if last>=0:
        line=line[0:last].strip()
    else:
        last = line.find("//")
        if last>=0:
            line = line[0:last].strip()
        else:
            line=line.strip()

    if len(line)==0:
        return None

    if line.startswith("#include"):
        return {'Include':line[8:].strip().strip(">").strip("<").strip('"'), 'Code':line.strip()}
    if line.startswith("#extends"):
        return {'Extends':line[8:].strip().strip(">").strip("<").strip('"'), 'Code':line.strip()}

    if last==-1:
        print "Can't find ';' in '"+fn+"', on line " + `ln`
        sys.exit(2)

    required = True
    if line.startswith("Required"):
        required = True
    elif line.startswith("Optional"):
        required = False
    else:
        print "Can't parse 'Required/Optional' tag in '"+fn+"', on line " + `ln`
        sys.exit(2)

    value = None
    type = ""
    name = ""
    if required==False:
        eq = line.find("=")
        if eq==-1:
            eq=last;
            value = '{}'
        else:
            value = line[eq+1:last]
        nameStart=line[0:eq].strip().rfind(" ")
        name = line[nameStart:eq].strip()
        type = line[9:nameStart].strip()
    else:
        nameStart=line[0:last].strip().rfind(" ")
        name = line[nameStart:last].strip()
        type = line[9:nameStart].strip()

    return {'Required':required, 'Type':type, 'Name':name, 'Value':value}

def ParseFile(filename):
    with open(filename) as f:
        lines = f.readlines()
    Data=[]
    Include=[]
    Extends=[]
    i=0
    optionalOnly=False
    for l in lines:
        i=i+1
        d=ParseLine(l,i,filename)
        if d!=None:
            if d.has_key('Required'):
                if d['Required']==False:
                    optionalOnly=True
                else:
                    if optionalOnly:
                        print "Required properties have to come before Optional ones, in '"+filename+"', on line " + `i`
                        sys.exit(2)
                Data.append(d)
            if d.has_key('Include'):
                Include.append(d['Code'])
            if d.has_key('Extends'):
                Extends.append(d['Extends'])
    return {"Data":Data,"Include":Include,"Extends":Extends}

def ContainsData(type,name,list):
    for d in list:
        if d['Type']==type and d['Name']==name:
            return d['Class']
    return False

def ContainsInclude(name,list):
    for d in list:
        if d==name:
            return True
    return False

def ContainsExtends(name,list):
    for d in list:
        if d==name:
            return True
    return False

def CollectExtensions(Input,SearchDirs,Content,ClassName):
    content = ParseFile(Input)
    if content.has_key('Extends'):
        for e in content['Extends']:
            if not ContainsExtends(e,Content['Extends']):
                file=None
                ext=e.split('/')
                for d in SearchDirs:
                    ff = d+'/share/'+ext[0]+'/init/'+ext[1]+'.in'
                    if os.path.isfile(ff):
                        file = ff
                        break
                if not file:
                    eprint("Cannot find extension '"+e+"'!")
                Content['Extends'].append(e)
                ChildClassName = os.path.basename(file[0:-3])
                Content = CollectExtensions(file,SearchDirs,Content,ChildClassName)
    if content.has_key('Data'):
      for d in content['Data']:
          cls = ContainsData(d['Type'],d['Name'],Content['Data'])
          if cls:
              print "Property '"+d['Type']+" "+d['Name']+" in "+Input+" hides the parent's ("+cls+") property with the same id."
              sys.exit(2)
          else:
              d['Class']=ClassName
              Content['Data'].append(d)
    if content.has_key('Include'):
        for i in content['Include']:
            if not ContainsInclude(i,Content['Include']):
                Content['Include'].append(i)
    return Content

def SortData(Data):
    a=[]
    b=[]
    for d in Data:
        if d['Required']:
            a.append(d)
        else:
            b.append(d)
    return a+b
def Generate(Input, Output, Namespace, ClassName,SearchDirs,DevelDir):
    print "Generating "+Output
    content = CollectExtensions(Input,SearchDirs,{'Data':[],'Include':[],'Extends':[]},ClassName)
    txt=Construct(Namespace,ClassName+"Initializer",SortData(content["Data"]),content["Include"])
    dir=os.path.dirname(Output)
    if not os.path.exists(dir):
        os.makedirs(dir)
    with open(Output,"w") as f:
        f.write(txt)


if __name__ == "__main__":
    if len(sys.argv)>4:
        offset=4
        n=(len(sys.argv)-offset)/2
        Namespace=sys.argv[1]
        SearchDirs=sys.argv[2].split(':')
        print SearchDirs
        DevelDir=sys.argv[3]
        if not os.path.exists(DevelDir+'/init'):
            os.makedirs(DevelDir+'/init')

        for i in range(0,n):
            Input = sys.argv[offset+i]
            ClassName = os.path.basename(sys.argv[offset+i][0:-3])
            with open(Input,"r") as fi:
                with open(DevelDir+'/init/'+ClassName+'.in',"w") as f:
                    f.write(fi.read())

        for i in range(0,n):
            Input = sys.argv[offset+i]
            Output = sys.argv[offset+n+i]
            ClassName = os.path.basename(sys.argv[offset+i][0:-3])
            Generate(Input,Output,Namespace,ClassName,SearchDirs,DevelDir)
    else:
      print "Initializer generation failure: invalid arguments!"
      sys.exit(1)